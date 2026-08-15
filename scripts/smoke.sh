#!/usr/bin/env bash
#
# Humo del stack ya levantado: comprueba lo que NINGÚN test unitario puede ver,
# porque solo existe en la frontera entre el código y su entorno.
#
# Cada comprobación de aquí corresponde a un fallo real que llegó al repo y
# sobrevivió a cuatro jobs de CI en verde (2026-08-15):
#
#   - Swagger UI devolvía 500 en el contenedor por `logo.jfif` vs `Logo.jfif`
#     (Linux distingue mayúsculas; con ManifestStaticFilesStorage eso tumba la
#     página entera).
#   - El catálogo se veía sin una sola foto: con DEBUG=False nadie servía /media/.
#   - El healthcheck del frontend fallaba 39 veces seguidas mientras la SPA
#     funcionaba perfectamente.
#
# Uso:
#   docker compose up --build -d
#   ./scripts/smoke.sh
#
# Variables: API_URL (default http://localhost:8000), WEB_URL (:5173),
#            ESPERA_MAX en segundos (default 180).

set -uo pipefail

API="${API_URL:-http://localhost:8000}"
WEB="${WEB_URL:-http://localhost:5173}"
ESPERA_MAX="${ESPERA_MAX:-180}"

fallos=0
ok()    { printf '  \033[32m✔\033[0m %s\n' "$1"; }
error() { printf '  \033[31m✖\033[0m %s\n' "$1"; fallos=$((fallos + 1)); }
titulo(){ printf '\n\033[1m%s\033[0m\n' "$1"; }

# --------------------------------------------------------------- utilidades

codigo_http() { curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$1"; }

espera_codigo() {  # <descripcion> <url> <codigo esperado>
  local desc="$1" url="$2" esperado="$3" obtenido
  obtenido="$(codigo_http "$url")"
  if [ "$obtenido" = "$esperado" ]; then
    ok "$desc ($esperado)"
  else
    error "$desc: esperaba $esperado y devolvió $obtenido → $url"
  fi
}

espera_contiene() {  # <descripcion> <url> <texto>
  local desc="$1" url="$2" texto="$3"
  if curl -s --max-time 15 "$url" | grep -q -- "$texto"; then
    ok "$desc"
  else
    error "$desc: la respuesta de $url no contiene «$texto»"
  fi
}

# --------------------------------------------- 1. los servicios están sanos

titulo "1. Salud de los contenedores"

# Antes de esperar nada, comprobar que se puede HABLAR con el compose. Sin esto,
# un fallo de configuración (p. ej. SECRET_KEY sin definir, que el compose exige
# al interpolar el YAML en cada invocación) se confunde con "el servicio todavía
# no arrancó" y el script se queda esperando su timeout completo por cada
# servicio antes de decir nada útil.
if ! salida="$(docker compose ps --format '{{.Service}}|{{.Health}}' 2>&1)"; then
  error "no se puede consultar el compose. ¿Falta alguna variable de entorno?"
  printf '  %s\n' "$salida"
  exit 1
fi
if [ -z "$salida" ]; then
  error "el compose no tiene servicios levantados: corré antes 'docker compose up -d'"
  exit 1
fi

# Se espera al healthcheck de Docker, no solo a que el puerto conteste: un
# healthcheck que miente bloquea `depends_on: service_healthy` y, con reinicio
# automático, tumba el servicio en bucle.
espera_healthy() {
  local servicio="$1" transcurrido=0 estado
  while [ "$transcurrido" -lt "$ESPERA_MAX" ]; do
    estado="$(docker compose ps --format '{{.Service}}|{{.Health}}' 2>/dev/null \
              | grep "^${servicio}|" | cut -d'|' -f2)"
    [ "$estado" = "healthy" ] && { ok "$servicio: healthy (${transcurrido}s)"; return 0; }
    sleep 3
    transcurrido=$((transcurrido + 3))
  done
  error "$servicio: no llegó a healthy en ${ESPERA_MAX}s (último estado: '${estado:-desconocido}')"
  docker compose logs --tail 30 "$servicio" || true
  return 1
}

espera_healthy db
espera_healthy backend
espera_healthy frontend

# ------------------------------------------------- 2. catálogo de demostración

titulo "2. Sembrar el catálogo"

if docker compose exec -T backend python manage.py cargar_productos 2>&1 | tee /tmp/seed.log | tail -3; then
  ok "cargar_productos terminó sin error"
  # El comando avisa —y no falla— cuando una imagen del CSV no existe.
  grep -q "SIN IMAGEN" /tmp/seed.log \
    && error "cargar_productos dejó productos sin imagen (¿el media no está montado?)"
else
  error "cargar_productos falló"
fi

# No basta con mirar la salida del comando: si los productos YA existían no
# intenta adjuntar ninguna imagen y el aviso nunca aparece, con lo que la
# comprobación anterior pasaría sin haber probado nada. Esto se contrasta contra
# el estado real, sirva o no la siembra.
sin_imagen="$(curl -s --max-time 15 "$API/api/v1/productos/?page_size=100" \
              | grep -o '"image":null' | wc -l | tr -d ' ')"
if [ "$sin_imagen" = "0" ]; then
  ok "ningún producto del catálogo quedó sin imagen"
else
  error "$sin_imagen producto(s) del catálogo no tienen imagen"
fi

# ------------------------------------------------------------ 3. la API responde

titulo "3. API"

espera_codigo   "healthz responde"            "$API/healthz/"            200
espera_contiene "healthz ve la base de datos" "$API/healthz/"            '"base_de_datos": "ok"'
espera_codigo   "catálogo v1"                 "$API/api/v1/productos/"   200
espera_contiene "el catálogo trae productos"  "$API/api/v1/productos/"   '"count"'

# El strangler-fig terminó: si alguien vuelve a colgar una app fuera de /api/v1/,
# aquí se entera.
espera_codigo   "las rutas v0 siguen retiradas" "$API/api/productos/productos/" 404

# --------------------------------------------- 4. estáticos y media (el 500 real)

titulo "4. Estáticos y media"

# Esta es la comprobación que habría cazado el `Logo.jfif`: con
# ManifestStaticFilesStorage, un nombre mal escrito devuelve 500, no 404.
espera_codigo "Swagger UI se renderiza" "$API/api/schema/swagger-ui/" 200
espera_codigo "el logo del Swagger existe en el manifiesto" "$API/static/swagger/Logo.jfif" 200
espera_codigo "esquema OpenAPI"        "$API/api/schema/"            200

# Y esta, el catálogo sin fotos: con DEBUG=False, /media/ solo se sirve si
# SERVE_MEDIA está activo.
imagen="$(curl -s --max-time 15 "$API/api/v1/productos/" \
          | grep -o 'http[^"]*/media/[^"]*' | head -1)"
if [ -n "$imagen" ]; then
  espera_codigo "la foto de un producto se sirve" "$imagen" 200
else
  error "ningún producto de la API trae URL de imagen"
fi

# ------------------------------------------------------------- 5. el frontend

titulo "5. Frontend"

espera_codigo   "la SPA se sirve"        "$WEB/"  200
espera_contiene "la SPA carga su bundle" "$WEB/"  '<script'
# nginx tiene que devolver index.html en las rutas del router, no un 404.
espera_codigo   "fallback de la SPA en una ruta del router" "$WEB/mis-compras" 200

# ------------------------------------------------------------------ resultado

titulo "Resultado"
if [ "$fallos" -eq 0 ]; then
  printf '  \033[32mTodas las comprobaciones pasaron.\033[0m\n\n'
  exit 0
fi
printf '  \033[31m%s comprobación(es) fallaron.\033[0m\n\n' "$fallos"
exit 1

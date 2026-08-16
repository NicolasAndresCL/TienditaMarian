#!/usr/bin/env bash
#
# Levanta el backend con la configuración de producción ESTRICTA y comprueba
# que se comporta bien detrás de un proxy que termina TLS — que es como va a
# correr en Render, Fly, Railway o cualquier VPS con Caddy delante.
#
# Por qué hace falta uno aparte de `smoke.sh`:
#
#   El compose local corre con `SECURE_HTTPS=False`, porque no hay TLS y con
#   `SECURE_SSL_REDIRECT` activo cada petición se redirigiría a https y no
#   respondería nada. O sea: la mitad del hardening de producción —redirección,
#   HSTS, cookies `Secure`, `SECURE_PROXY_SSL_HEADER`— **nunca se ejecuta** en
#   ninguna verificación. `check --deploy` solo mira que los settings estén
#   puestos; no comprueba que la aplicación siga respondiendo con ellos.
#
# El fallo que busca es el más común de Django detrás de un proxy: el proxy
# habla http con la aplicación, la aplicación no reconoce `X-Forwarded-Proto`,
# responde 301 a https, el proxy vuelve a entrar por http… bucle infinito. El
# sitio queda caído con los settings "correctos" y `check --deploy` en verde.
#
#   docker compose up -d db          # hace falta la base
#   ./scripts/humo-produccion.sh
#
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUERTO="${PUERTO_HUMO_PROD:-8099}"
BASE="http://localhost:$PUERTO"
CONTENEDOR="tiendita-humo-produccion"

fallos=0
paso()   { printf '\n\033[1m▶ %s\033[0m\n' "$1"; }
ok()     { printf '  \033[32m✔\033[0m %s\n' "$1"; }
error()  { printf '  \033[31m✖\033[0m %s\n' "$1"; fallos=$((fallos + 1)); }

comprobar() {  # <descripcion> <esperado> <obtenido>
  if [ "$2" = "$3" ]; then ok "$1"; else error "$1 (esperaba «$2», llegó «$3»)"; fi
}

limpiar() {
  MSYS_NO_PATHCONV=1 docker rm -f "$CONTENEDOR" > /dev/null 2>&1 || true
}
trap limpiar EXIT

cd "$RAIZ" || exit 1

# ------------------------------------------------------------------ arranque

paso "Levantando el backend con SECURE_HTTPS=True"

limpiar
# `SERVE_MEDIA=False` porque en un despliegue real el media lo sirve un CDN o
# nginx, no Django. Aquí importa que la aplicación arranque igual sin esa ruta.
if ! MSYS_NO_PATHCONV=1 docker compose run --rm -d --name "$CONTENEDOR" \
      -p "$PUERTO:8000" \
      -e SECURE_HTTPS=True \
      -e SERVE_MEDIA=False \
      -e ALLOWED_HOSTS=localhost,127.0.0.1 \
      backend > /dev/null 2>&1; then
  error "no se pudo levantar el contenedor"
  exit 1
fi

# Se espera al hecho —que responda— y no a un `sleep` arbitrario. La petición
# lleva la cabecera del proxy: sin ella todo contesta 301 y no probaría nada.
intentos=0
until curl -fsS -o /dev/null -H "X-Forwarded-Proto: https" "$BASE/healthz/" 2>/dev/null; do
  intentos=$((intentos + 1))
  if [ "$intentos" -gt 60 ]; then
    error "el backend no respondió en 60 intentos"
    MSYS_NO_PATHCONV=1 docker logs "$CONTENEDOR" 2>&1 | tail -25
    exit 1
  fi
  sleep 2
done
ok "arrancó y responde (migrate + collectstatic + gunicorn)"

# --------------------------------------------------- comportamiento tras proxy

paso "Detrás de un proxy que termina TLS"

# 1. Con la cabecera del proxy: la aplicación tiene que dar por buena la
#    petición y NO redirigir. Si aquí sale 301, en producción hay bucle.
codigo=$(curl -s -o /dev/null -w '%{http_code}' \
  -H "X-Forwarded-Proto: https" "$BASE/healthz/")
comprobar "con X-Forwarded-Proto: https responde 200 (sin bucle)" "200" "$codigo"

# 2. Sin la cabecera: es tráfico http de verdad y sí debe redirigir.
codigo=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/healthz/")
comprobar "sin la cabecera redirige a https (301)" "301" "$codigo"

destino=$(curl -s -o /dev/null -w '%{redirect_url}' "$BASE/healthz/")
case "$destino" in
  https://*) ok "la redirección apunta a https" ;;
  *)         error "la redirección no va a https: «$destino»" ;;
esac

paso "Cabeceras de seguridad"

cabeceras=$(curl -s -D - -o /dev/null -H "X-Forwarded-Proto: https" "$BASE/healthz/")

if grep -qi "^strict-transport-security:.*max-age=31536000" <<< "$cabeceras"; then
  ok "HSTS con max-age de un año"
else
  error "falta HSTS (o el max-age no es el esperado)"
fi

if grep -qi "^x-content-type-options: *nosniff" <<< "$cabeceras"; then
  ok "X-Content-Type-Options: nosniff"
else
  error "falta X-Content-Type-Options"
fi

if grep -qi "^x-frame-options: *DENY" <<< "$cabeceras"; then
  ok "X-Frame-Options: DENY"
else
  error "falta X-Frame-Options"
fi

paso "Cookies de sesión con Secure"

# Se registra una usuaria de verdad: es la respuesta que planta las tres cookies
# a la vez. `/auth/me/` NO sirve para esto — sin sesión contesta 401 antes de que
# `ensure_csrf_cookie` llegue a ejecutarse, así que no planta nada.
usuaria="humo_prod_$(date +%s)"
cookies=$(curl -s -D - -o /dev/null \
  -H "X-Forwarded-Proto: https" -H "Content-Type: application/json" \
  -d "{\"username\":\"$usuaria\",\"email\":\"$usuaria@ejemplo.cl\",\"password\":\"Tiendita-2026-Segura\",\"password_confirm\":\"Tiendita-2026-Segura\"}" \
  "$BASE/api/v1/auth/register/")

for cookie in csrftoken tiendita_access tiendita_refresh; do
  linea=$(grep -i "^set-cookie: *$cookie=" <<< "$cookies")
  if [ -z "$linea" ]; then
    error "no se plantó la cookie $cookie"
  elif grep -qi "Secure" <<< "$linea"; then
    ok "$cookie sale con el flag Secure"
  else
    error "$cookie sale SIN Secure: viajaría en claro por http"
  fi
done

# Las dos de sesión, además, tienen que ser invisibles al JavaScript: es lo que
# impide que un XSS se lleve la sesión. El csrftoken NO lleva HttpOnly a
# propósito — el frontend tiene que poder leerlo para mandarlo de vuelta.
for cookie in tiendita_access tiendita_refresh; do
  if grep -i "^set-cookie: *$cookie=" <<< "$cookies" | grep -qi "HttpOnly"; then
    ok "$cookie es HttpOnly"
  else
    error "$cookie NO es HttpOnly: el JavaScript de la página podría leerla"
  fi
done

paso "La API sigue en pie"

codigo=$(curl -s -o /dev/null -w '%{http_code}' \
  -H "X-Forwarded-Proto: https" "$BASE/api/v1/productos/")
comprobar "catálogo público responde 200" "200" "$codigo"

codigo=$(curl -s -o /dev/null -w '%{http_code}' \
  -H "X-Forwarded-Proto: https" "$BASE/api/schema/swagger-ui/")
comprobar "Swagger UI se renderiza con los estáticos comprimidos" "200" "$codigo"

# Con SERVE_MEDIA=False Django NO publica /media/: es lo correcto en producción
# (lo sirve un CDN), pero conviene dejarlo dicho en voz alta, porque es el
# recordatorio de que las fotos necesitan almacenamiento externo.
codigo=$(curl -s -o /dev/null -w '%{http_code}' \
  -H "X-Forwarded-Proto: https" "$BASE/media/productos/images/no-existe.jpg")
if [ "$codigo" = "404" ]; then
  ok "con SERVE_MEDIA=False nadie sirve /media/ (lo hará el CDN)"
else
  error "/media/ contestó $codigo con SERVE_MEDIA=False"
fi

# ------------------------------------------------------------------ resultado

printf '\n\033[1mResultado\033[0m\n'
if [ "$fallos" -eq 0 ]; then
  printf '  \033[32mLa configuración de producción arranca y se comporta bien tras un proxy.\033[0m\n\n'
  exit 0
fi
printf '  \033[31m%s comprobación(es) fallaron.\033[0m\n\n' "$fallos"
exit 1

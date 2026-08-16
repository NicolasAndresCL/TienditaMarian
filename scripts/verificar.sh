#!/usr/bin/env bash
#
# Reproduce en local lo que hace el CI, para no descubrir un fallo después de
# pushear.
#
# Existe porque pasó: tres corridas seguidas en rojo por warnings de
# drf-spectacular que `check --deploy --fail-level WARNING` convierte en fallo
# del build. `pytest` y `ruff` estaban en verde, así que en local todo "pasaba" —
# el job que fallaba era justamente el único que yo no ejecutaba.
#
# Un paso obligatorio que hay que acordarse de hacer no es obligatorio: es un
# recordatorio. Esto lo convierte en un comando.
#
#   ./scripts/verificar.sh            # todo
#   ./scripts/verificar.sh backend    # solo backend
#   ./scripts/verificar.sh frontend   # solo frontend
#   ./scripts/verificar.sh entorno    # el frontend DENTRO de node:24, como el CI
#
# El modo `entorno` existe por un segundo fallo, distinto del anterior: la suite
# del frontend pasaba aquí y fallaba en el pipeline porque `frontend/.env` está
# en .gitignore —o sea, en CI NO existe— y `VITE_API_BASE_URL` quedaba en
# `undefined`. Ninguna corrida local podía verlo, porque en local sí hay `.env`.
# Correr los tests en una imagen limpia reproduce el checkout del CI de verdad:
# sin `.env`, con `npm ci` y con la misma versión de Node.
#
# No cubre el job `docker-smoke` (construir las imágenes y levantar el stack):
# para eso está `docker compose up --build -d && ./scripts/smoke.sh`.

set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUE="${1:-todo}"

PY="$RAIZ/backend/env/Scripts/python.exe"       # Windows
[ -x "$PY" ] || PY="$RAIZ/backend/env/bin/python"  # Linux / macOS

fallos=0
paso()   { printf '\n\033[1m▶ %s\033[0m\n' "$1"; }
ok()     { printf '  \033[32m✔\033[0m %s\n' "$1"; }
error()  { printf '  \033[31m✖\033[0m %s\n' "$1"; fallos=$((fallos + 1)); }

ejecutar() {  # <descripcion> <comando...>
  local desc="$1"; shift
  if "$@" > /tmp/verificar.log 2>&1; then
    ok "$desc"
  else
    error "$desc"
    tail -25 /tmp/verificar.log | sed 's/^/    /'
  fi
}

# ------------------------------------------------------------------ backend

if [ "$QUE" = "todo" ] || [ "$QUE" = "backend" ]; then
  if [ ! -x "$PY" ]; then
    error "no encuentro el venv del backend (backend/env). Creálo antes."
  else
    cd "$RAIZ/backend" || exit 1
    export PYTHONIOENCODING=utf-8

    paso "Backend — lint (ruff)"
    ejecutar "ruff check ." "$PY" -m ruff check .

    paso "Backend — tests + cobertura"
    ejecutar "pytest --cov-fail-under=90" "$PY" -m pytest -q --cov --cov-fail-under=90

    paso "Backend — hardening de despliegue"
    # Este es el que se saltaba. Corre contra la config de PRODUCCIÓN, con una
    # clave efímera: `check --deploy` rechaza claves débiles y fallaría por la
    # clave en vez de por el hardening real.
    #
    # Las variables van por `env` y NO en una subshell. Con `( export …; ejecutar
    # … ) || fallos=…` este paso podía fallar y el script terminaba anunciando
    # "Todo en verde": `fallos` se incrementaba dentro de la subshell —una copia
    # que muere con ella— y el `||` nunca se disparaba, porque `ejecutar` devuelve
    # 0 aunque el comando falle (su última sentencia es una asignación). Un
    # verificador que informa verde sobre un fallo es peor que no tenerlo: da
    # permiso para pushear. Pasó de verdad, con el `mail.E001` de Django 6.1.
    #
    # `DJANGO_ENV_FILE` apunta a un archivo inexistente para que NO se lea
    # `backend/.env`: en el runner del CI ese archivo no existe, y el de acá es
    # de desarrollo. Sin esto, la comprobación de producción se hacía sobre la
    # configuración de desarrollo — misma lección que con el `.env` del frontend:
    # hay que reproducir el checkout, no solo los comandos.
    SECRET_KEY_EFIMERA="$("$PY" -c 'import secrets; print(secrets.token_urlsafe(64))')"
    ejecutar "check --deploy --fail-level WARNING" \
      env DJANGO_ENV_FILE="$RAIZ/backend/.env.que-no-existe" \
          DJANGO_SETTINGS_MODULE=config.settings.prod \
          ALLOWED_HOSTS=tienditademarian.com \
          DATABASE_URL=sqlite:///db.sqlite3 \
          SECURE_HTTPS=True \
          SECRET_KEY="$SECRET_KEY_EFIMERA" \
          "$PY" manage.py check --deploy --fail-level WARNING
  fi
fi

# ----------------------------------------------------------------- frontend

if [ "$QUE" = "todo" ] || [ "$QUE" = "frontend" ]; then
  cd "$RAIZ/frontend" || exit 1

  paso "Frontend — lint (eslint)"
  ejecutar "npm run lint" npm run lint

  paso "Frontend — tests (vitest)"
  ejecutar "npm test" npm test

  paso "Frontend — build (vite)"
  ejecutar "npm run build" npm run build
fi

# -------------------------------------------------- el frontend como en el CI

if [ "$QUE" = "entorno" ]; then
  cd "$RAIZ/frontend" || exit 1

  paso "Frontend — en node:24 y sin .env (checkout limpio, como el CI)"

  if ! docker info > /dev/null 2>&1; then
    error "Docker no está corriendo; no se puede reproducir el entorno del CI"
  else
    # La imagen COPIA el código en vez de montarlo: un bind mount desde Windows
    # tiene un I/O tan lento que los workers de vitest se cuelgan, y eso enmascara
    # el resultado real. El .dockerignore ya deja fuera .env y node_modules, que
    # es justo lo que se quiere: un checkout limpio.
    cat > .Dockerfile.verificar <<'DOCKER'
FROM node:24-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --silent
COPY . .
CMD ["npx", "vitest", "run"]
DOCKER

    if MSYS_NO_PATHCONV=1 docker build -q -f .Dockerfile.verificar -t tiendita-verificar-front . > /dev/null 2>&1; then
      ejecutar "vitest en node:24 sin .env" \
        env MSYS_NO_PATHCONV=1 docker run --rm --cpus=2 tiendita-verificar-front
    else
      error "no se pudo construir la imagen de verificación"
    fi

    rm -f .Dockerfile.verificar
  fi
fi

# ------------------------------------------------------------------ resultado

printf '\n\033[1mResultado\033[0m\n'
if [ "$fallos" -eq 0 ]; then
  printf '  \033[32mTodo en verde. El CI debería pasar.\033[0m\n\n'
  exit 0
fi
printf '  \033[31m%s verificación(es) fallaron: NO pushees todavía.\033[0m\n\n' "$fallos"
exit 1

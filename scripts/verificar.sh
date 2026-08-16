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
#   ./scripts/verificar.sh entorno    # el frontend DENTRO de node:20, como el CI
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
    (
      export DJANGO_SETTINGS_MODULE=config.settings.prod
      export ALLOWED_HOSTS=tienditademarian.com
      export DATABASE_URL=sqlite:///db.sqlite3
      export SECURE_HTTPS=True
      SECRET_KEY="$("$PY" -c 'import secrets; print(secrets.token_urlsafe(64))')"
      export SECRET_KEY
      ejecutar "check --deploy --fail-level WARNING" \
        "$PY" manage.py check --deploy --fail-level WARNING
    ) || fallos=$((fallos + 1))
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

  paso "Frontend — en node:20 y sin .env (checkout limpio, como el CI)"

  if ! docker info > /dev/null 2>&1; then
    error "Docker no está corriendo; no se puede reproducir el entorno del CI"
  else
    # La imagen COPIA el código en vez de montarlo: un bind mount desde Windows
    # tiene un I/O tan lento que los workers de vitest se cuelgan, y eso enmascara
    # el resultado real. El .dockerignore ya deja fuera .env y node_modules, que
    # es justo lo que se quiere: un checkout limpio.
    cat > .Dockerfile.verificar <<'DOCKER'
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --silent
COPY . .
CMD ["npx", "vitest", "run"]
DOCKER

    if MSYS_NO_PATHCONV=1 docker build -q -f .Dockerfile.verificar -t tiendita-verificar-front . > /dev/null 2>&1; then
      ejecutar "vitest en node:20 sin .env" \
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

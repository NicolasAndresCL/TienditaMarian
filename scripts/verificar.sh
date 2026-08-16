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

# ------------------------------------------------------------------ resultado

printf '\n\033[1mResultado\033[0m\n'
if [ "$fallos" -eq 0 ]; then
  printf '  \033[32mTodo en verde. El CI debería pasar.\033[0m\n\n'
  exit 0
fi
printf '  \033[31m%s verificación(es) fallaron: NO pushees todavía.\033[0m\n\n' "$fallos"
exit 1

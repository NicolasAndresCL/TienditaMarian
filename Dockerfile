# Imagen de producción: multi-stage y sin root (skill §4).
#
# El build compila las dependencias en un stage aparte y solo se copia el
# resultado, así la imagen final no arrastra compiladores ni cabeceras de
# desarrollo: menos peso y menos superficie de ataque.

# ---------------------------------------------------------------- build
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements/prod.txt

# ---------------------------------------------------------------- runtime
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod

# libpq5 es la librería en tiempo de ejecución de PostgreSQL (sin las cabeceras
# de desarrollo, que solo hacían falta para compilar). curl, para el healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Un proceso comprometido dentro del contenedor no debe ser root.
RUN useradd --create-home --shell /bin/bash tiendita

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=tiendita:tiendita . .

RUN mkdir -p /app/staticfiles /app/media \
    && chown -R tiendita:tiendita /app/staticfiles /app/media

USER tiendita

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz/ || exit 1

# WhiteNoise sirve los estáticos, así que no hace falta un nginx delante.
CMD ["sh", "-c", "python manage.py migrate --no-input && \
     python manage.py collectstatic --no-input && \
     gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60"]

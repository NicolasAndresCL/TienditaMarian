"""Entorno de producción.

Objetivo: `python manage.py check --deploy` sin warnings.
"""

from .base import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # noqa: F405  — obligatorio, sin default

# WhiteNoise sirve los estáticos sin depender de un nginx delante.
MIDDLEWARE.insert(  # noqa: F405
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,  # noqa: F405
    "whitenoise.middleware.WhiteNoiseMiddleware",
)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Se togglea con SECURE_HTTPS para poder correr la imagen detrás de un proxy que
# aún no tiene TLS, sin tener que tocar el código.
SECURE_HTTPS = env.bool("SECURE_HTTPS", default=True)  # noqa: F405

SECURE_SSL_REDIRECT = SECURE_HTTPS
SESSION_COOKIE_SECURE = SECURE_HTTPS
CSRF_COOKIE_SECURE = SECURE_HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if SECURE_HTTPS else None

SECURE_HSTS_SECONDS = 31536000 if SECURE_HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HTTPS
SECURE_HSTS_PRELOAD = SECURE_HTTPS

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

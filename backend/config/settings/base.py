"""Configuración común a todos los entornos.

Nunca se usa directamente: `dev`, `prod` y `test` heredan de aquí con
`from .base import *`. Esa herencia es deliberada — la versión anterior tenía un
`settings_test.py` autónomo que había divergido de producción (corría sin DRF y,
por tanto, con `AllowAny`), de modo que la suite validaba una aplicación que no
era la que se desplegaba.
"""

from datetime import timedelta
from pathlib import Path

import dj_database_url
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "drf_spectacular_sidecar",
]

LOCAL_APPS = [
    "apps.analytics",
    "apps.auditlog",
    "apps.auth_api",
    "apps.carrito",
    "apps.descuentos",
    "apps.envios",
    "apps.notificaciones",
    "apps.orden",
    "apps.pagos",
    "apps.productos",
    "apps.reviews",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Después de AuthenticationMiddleware: necesita `request.user` ya resuelto
    # para que el auditlog sepa quién hizo cada cambio.
    "core.middleware.UsuarioActualMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Una sola variable describe la conexión completa (motor, credenciales, host y
# puerto). Antes el nombre de la base, el host y el puerto estaban escritos a
# mano en el settings y solo el usuario y la contraseña venían del entorno.
DATABASES = {
    "default": dj_database_url.config(
        default=env("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=env.int("DB_CONN_MAX_AGE", default=60),
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Django sirve /media/ por su cuenta solo con DEBUG=True, y WhiteNoise sirve los
# estáticos pero NO el media subido: con DEBUG=False las fotos del catálogo daban
# 404 sin que nada lo avisara. Esta bandera publica la ruta explícitamente (ver
# config/urls.py) para el compose local y las demos.
# En un despliegue real va en False: el media se sirve por nginx o un CDN.
SERVE_MEDIA = env.bool("SERVE_MEDIA", default=False)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Acepta la sesión por cookie httpOnly (el navegador) y por cabecera Bearer
    # (Swagger y clientes de API). Ver core/api/authentication.py.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.api.authentication.JWTCookieAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Único punto donde un error se convierte en respuesta HTTP: traduce las
    # excepciones de dominio (core.exceptions) y unifica el formato de todos los
    # errores de la API.
    "EXCEPTION_HANDLER": "core.api.exception_handler.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "300/min",
        # Perfil propio para el login: es el endpoint que se ataca por fuerza bruta.
        "login": "10/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Con rotación + blacklist el logout invalida el refresh de verdad.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Tiendita de Marian API",
    "DESCRIPTION": (
        "API REST de la Tiendita de Marian: catálogo, carrito, checkout transaccional, "
        "órdenes, pagos, envíos, descuentos, reseñas y auditoría de eventos. "
        "Autenticación JWT y esquema OpenAPI 3.0."
    ),
    "VERSION": "1.0.0",
    "CONTACT": {"name": "Soporte de la Tiendita", "email": "nicolas.cano.leal@gmail.com"},
    "LICENSE": {"name": "Licencia MIT", "url": "https://opensource.org/licenses/MIT"},
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": True,
    # Hubo aquí un PREPROCESSING_HOOK que excluía del esquema las rutas v0: al
    # compartir vista con sus equivalentes v1 duplicaban el operationId y
    # generaban ~46 warnings W001 que hacían fallar `check --deploy
    # --fail-level WARNING`. Borradas las v0, el hook sobraba.
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "displayRequestDuration": True,
        "filter": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
}

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:5173", "http://127.0.0.1:5173"]
)
# La sesión viaja en cookies, y el navegador no las manda a otro origen salvo que
# el servidor lo autorice explícitamente. Sin esto, el frontend de :5173 no
# recibiría la cookie del backend de :8000 ni la reenviaría.
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------- sesión JWT
#
# Los tokens viajan en cookies HttpOnly: el JavaScript de la página no puede
# leerlos, así que un XSS ya no se lleva la sesión. Ver
# `core/api/authentication.py` para la contrapartida (CSRF).
JWT_COOKIE_ACCESS = "tiendita_access"
JWT_COOKIE_REFRESH = "tiendita_refresh"

# `Secure` exige HTTPS. En desarrollo va en False porque localhost es http; en
# producción tiene que ser True o la cookie viaja en claro.
JWT_COOKIE_SECURE = env.bool("JWT_COOKIE_SECURE", default=not DEBUG)

# `Lax` basta mientras el frontend y la API compartan sitio registrable
# (localhost:5173 → localhost:8000, o tienditademarian.com → api.tienditademarian.com):
# el puerto y el subdominio no cambian el "sitio" a efectos de cookies. Si algún
# día el frontend vive en OTRO dominio (Netlify, Vercel), hará falta
# `None` + `Secure`, que a su vez exige HTTPS en ambos extremos.
JWT_COOKIE_SAMESITE = env("JWT_COOKIE_SAMESITE", default="Lax")

# El refresh solo se manda a las rutas que lo necesitan: así no viaja en cada
# petición al catálogo, reduciendo su exposición.
JWT_COOKIE_REFRESH_PATH = "/api/v1/auth/"

# El frontend lee esta cookie (NO httpOnly, a propósito) para poner la cabecera
# `X-CSRFToken`; es el mecanismo estándar de Django.
CSRF_COOKIE_NAME = "csrftoken"
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"

# Django rechaza una petición que escribe si su cabecera `Origin` no coincide con
# el host ni está en esta lista. El frontend vive en otro puerto (:5173 → :8000),
# así que sin esto toda escritura moriría con "Origin checking failed" en cuanto
# la sesión pasó a viajar en cookies. Por defecto, los mismos orígenes que ya
# están autorizados para CORS: son el mismo frontend.
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=CORS_ALLOWED_ORIGINS)

# ------------------------------------------------------------------- Webpay
#
# Credenciales del ambiente de INTEGRACIÓN de Transbank, que son públicas y las
# publica el propio SDK: sirven para desarrollar sin contrato de comercio. En
# producción se sustituyen por las reales y `WEBPAY_PRODUCCION=True`.
WEBPAY_COMMERCE_CODE = env("WEBPAY_COMMERCE_CODE", default="597055555532")
WEBPAY_API_KEY = env(
    "WEBPAY_API_KEY",
    default="579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C",
)
WEBPAY_PRODUCCION = env.bool("WEBPAY_PRODUCCION", default=False)

# A dónde vuelve la clienta desde Transbank. Es una URL del BACKEND, no del
# frontend: la vuelta es un POST y hay que confirmar la transacción antes de
# enseñar nada.
WEBPAY_URL_RETORNO = env(
    "WEBPAY_URL_RETORNO", default="http://localhost:8000/api/v1/pagos/webpay/retorno/"
)
# Y a dónde se redirige después, ya con el resultado.
WEBPAY_URL_FRONTEND = env("WEBPAY_URL_FRONTEND", default="http://localhost:5173")

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@tienditademarian.com")
CONTACTO_EMAIL = env("CONTACTO_EMAIL", default="contacto@tienditademarian.com")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        # Los módulos del proyecto usan `logging.getLogger(__name__)`, así que
        # cuelgan todos de estos dos raíces.
        "apps": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO"), "propagate": False},
        "core": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO"), "propagate": False},
    },
}

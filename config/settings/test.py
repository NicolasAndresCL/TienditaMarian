"""Entorno de tests.

Hereda de `base`, así que los tests corren con **los mismos** INSTALLED_APPS,
autenticación JWT y permisos (`IsAuthenticated`) que producción. Solo se cambia
la infraestructura (base de datos, correo, hashing) para que la suite sea rápida
y no toque nada externo.

Los valores por defecto se inyectan en `os.environ` *antes* de importar `base`
para que la suite corra en un checkout limpio sin `.env` (así funciona en CI).
"""

import os

os.environ.setdefault("SECRET_KEY", "test-insecure-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")
os.environ.setdefault("DEBUG", "False")

from .base import *  # noqa: E402, F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Hashing rápido: los tests crean muchos usuarios y no medimos criptografía.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# El throttling se prueba en su propio test; dejarlo activo en toda la suite solo
# produciría 429 espurios al encadenar peticiones. Los scopes se mantienen con
# valor None (y no se borran) porque DRF lanza ImproperlyConfigured si una vista
# declara un scope que no existe en el diccionario.
REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {"anon": None, "user": None, "login": None},
}

# Los tests no deben depender de la conexión persistente.
DATABASES["default"]["CONN_MAX_AGE"] = 0

LOGGING["root"]["level"] = "WARNING"  # noqa: F405

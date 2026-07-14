"""Entorno de tests.

Hereda de `base`, así que los tests corren con **los mismos** INSTALLED_APPS,
autenticación JWT y permisos (`IsAuthenticated`) que producción. Solo se cambia
la infraestructura (base de datos, correo, hashing) para que la suite sea rápida
y no toque nada externo.

Los valores por defecto se inyectan en `os.environ` *antes* de importar `base`
para que la suite corra en un checkout limpio, sin `.env` ni secretos (así es
como funciona en CI).
"""

import os

os.environ.setdefault("SECRET_KEY", "test-insecure-key-not-for-production")
os.environ.setdefault("DEBUG", "False")

# Por defecto, SQLite en memoria: la suite corre en un segundo y sin instalar
# nada. Pero si el entorno trae un DATABASE_URL, gana ese — es lo que permite
# ejecutar la misma suite contra PostgreSQL, donde `select_for_update` existe de
# verdad y el test de concurrencia del checkout sí prueba el bloqueo.
os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")

from .base import *  # noqa: E402, F403

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Hashing rápido: la suite crea muchos usuarios y aquí no medimos criptografía.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# El throttling tiene su propio test; dejarlo activo en toda la suite solo
# produciría 429 espurios al encadenar peticiones. Los scopes se conservan con
# valor None (en vez de borrarse) porque DRF lanza ImproperlyConfigured si una
# vista declara un scope que no está en el diccionario.
REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {"anon": None, "user": None, "login": None},
}

# Sin conexión persistente entre tests.
DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405

LOGGING["root"]["level"] = "WARNING"  # noqa: F405

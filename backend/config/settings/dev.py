"""Entorno de desarrollo local."""

from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0"]

# MailHog en localhost:1025 si está levantado; si no, los correos salen por consola.
# El `MAILERS` de `base` ya lee `EMAIL_BACKEND` del entorno con este mismo
# default, así que aquí no hay nada que reescribir: la línea que había era una
# copia literal de la de `base`.

"""Settings por entorno.

Se elige con `DJANGO_SETTINGS_MODULE`:

    config.settings.dev    desarrollo local (default de manage.py)
    config.settings.prod   producción (default de wsgi/asgi)
    config.settings.test   suite de tests

Los tres heredan de `config.settings.base`.
"""

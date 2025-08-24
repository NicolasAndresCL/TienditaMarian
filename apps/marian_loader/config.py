"""
Configuraciones por defecto para marian_loader.
Sobrescribibles desde settings.py en la clave MARIAN_LOADER.
"""

from django.conf import settings

DEFAULTS = {
    'CSV_CHUNK_SIZE': 200,
    'TIMEOUT_SECONDS': 300,
    'REPORT_FORMATS': ['markdown'],
}

USER_CONFIG = getattr(settings, 'MARIAN_LOADER', {})
CFG = {**DEFAULTS, **USER_CONFIG}

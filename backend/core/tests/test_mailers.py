"""El `MAILERS` de Django 6.1 se puede construir con CADA backend que usamos.

Django 6.1 sustituyó los `EMAIL_*` sueltos por un `MAILERS` con la forma de
`DATABASES`, y de paso los volvió **estrictos**: las `OPTIONS` se validan contra
el backend y una que no reconozca aborta con
`InvalidMailer: Unknown options 'host', 'port'…`. Antes daba igual — `EMAIL_HOST`
existía siempre y lo leía quien lo necesitara.

El resultado fue que pasar `host`/`port` con el backend de **consola**, que es el
de desarrollo por defecto, reventaba en el primer correo. El resto de la suite no
podía verlo: corre con el backend en memoria y sin ninguna opción.

Por eso estos tests no comprueban que se envíe un correo, sino que el mailer se
pueda **construir** con la combinación de backend y opciones que produce
`config/settings/base.py` para cada entorno real:

- consola  → desarrollo sin MailHog
- SMTP     → Docker (MailHog) y producción
- locmem   → la propia suite
"""

import importlib

import pytest
from django.core.mail import mailers
from django.test import override_settings

CONSOLA = "django.core.mail.backends.console.EmailBackend"
SMTP = "django.core.mail.backends.smtp.EmailBackend"
MEMORIA = "django.core.mail.backends.locmem.EmailBackend"


def _mailers_de_base(monkeypatch, backend: str) -> dict:
    """Los MAILERS que `base.py` produciría con ese `EMAIL_BACKEND`.

    Se recarga el módulo en vez de copiar aquí la regla: si mañana alguien la
    cambia, este test se entera. Copiarla lo dejaría probando su propia copia.
    """
    monkeypatch.setenv("EMAIL_BACKEND", backend)

    import config.settings.base as base

    importlib.reload(base)
    return base.MAILERS


@pytest.mark.parametrize("backend", [CONSOLA, SMTP, MEMORIA])
def test_el_mailer_se_construye_con_cada_backend(monkeypatch, backend):
    configuracion = _mailers_de_base(monkeypatch, backend)

    with override_settings(MAILERS=configuracion):
        # Pedir la conexión es lo que dispara la validación de las OPTIONS.
        conexion = mailers["default"]

    assert conexion is not None


def test_solo_el_backend_smtp_recibe_host_y_puerto(monkeypatch):
    """La regla, dicha en voz alta: las opciones de SMTP son para SMTP."""
    con_smtp = _mailers_de_base(monkeypatch, SMTP)["default"]["OPTIONS"]
    con_consola = _mailers_de_base(monkeypatch, CONSOLA)["default"]["OPTIONS"]

    assert con_smtp["host"]
    assert con_smtp["port"]
    assert con_consola == {}


@pytest.fixture(autouse=True)
def _restaurar_base():
    """Deja `base` como estaba: los demás tests importan de ese módulo."""
    yield

    import config.settings.base as base

    importlib.reload(base)

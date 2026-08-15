"""Colocación y borrado de las cookies de sesión.

Un único sitio decide cómo se escriben: si los flags viven repartidos por las
vistas, tarde o temprano una se olvida el `httponly` y nadie lo nota hasta que
alguien lee el token desde la consola del navegador.
"""

from __future__ import annotations

from django.conf import settings
from rest_framework.response import Response

# El refresh dura 7 días y el access 15 minutos; la cookie caduca con su token
# para que el navegador no guarde credenciales muertas.
_VIDA_ACCESS = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
_VIDA_REFRESH = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())


def poner_sesion(respuesta: Response, access: str, refresh: str | None = None) -> Response:
    """Escribe las cookies de sesión en la respuesta."""
    respuesta.set_cookie(
        settings.JWT_COOKIE_ACCESS,
        access,
        max_age=_VIDA_ACCESS,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
    )

    if refresh is not None:
        respuesta.set_cookie(
            settings.JWT_COOKIE_REFRESH,
            refresh,
            max_age=_VIDA_REFRESH,
            httponly=True,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
            # Acotado a /api/v1/auth/: el refresh no tiene por qué viajar en cada
            # petición al catálogo.
            path=settings.JWT_COOKIE_REFRESH_PATH,
        )

    return respuesta


def quitar_sesion(respuesta: Response) -> Response:
    """Borra las cookies de sesión.

    El `path` tiene que coincidir con el que se usó al ponerlas o el navegador
    ignora el borrado y la cookie sobrevive al logout.
    """
    respuesta.delete_cookie(settings.JWT_COOKIE_ACCESS)
    respuesta.delete_cookie(
        settings.JWT_COOKIE_REFRESH, path=settings.JWT_COOKIE_REFRESH_PATH
    )
    return respuesta

"""Usuario actual accesible fuera del ciclo request/response.

El auditlog se dispara desde señales del ORM, donde no hay `request` a mano. Sin
esto, cada entrada quedaba con `user=None` — una bitácora de auditoría que no
registraba a nadie.

Se usa `ContextVar` y no una variable global de módulo porque aísla el valor por
contexto de ejecución: hilos y tareas async no se pisan entre sí.
"""

from __future__ import annotations

import contextvars
from collections.abc import Callable
from typing import TYPE_CHECKING

from django.http import HttpRequest, HttpResponse

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

_usuario_actual: contextvars.ContextVar[AbstractBaseUser | None] = contextvars.ContextVar(
    "usuario_actual", default=None
)


def get_usuario_actual() -> AbstractBaseUser | None:
    """Usuario autenticado de la petición en curso, o None.

    Devuelve None también para peticiones anónimas y para código que corre fuera
    de una petición (comandos de management, shell, tareas de fondo).
    """
    usuario = _usuario_actual.get()
    if usuario is None or not usuario.is_authenticated:
        return None
    return usuario


class UsuarioActualMiddleware:
    """Publica `request.user` en un ContextVar durante la petición."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        token = _usuario_actual.set(getattr(request, "user", None))
        try:
            return self.get_response(request)
        finally:
            # Siempre se restaura, incluso si la vista lanza: de lo contrario el
            # worker quedaría "pegado" con el usuario de la petición anterior.
            _usuario_actual.reset(token)

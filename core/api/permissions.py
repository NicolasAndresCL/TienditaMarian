"""Permisos reutilizables.

`IsAuthenticated` solo responde "¿quién eres?". No responde "¿esto es tuyo?", y
esa confusión era el origen de los agujeros de la API: con `queryset =
Envio.objects.all()` y `IsAuthenticated`, cualquier cliente registrado podía leer
—y editar— los envíos de todos los demás, con su dirección incluida.

Un permiso a nivel de objeto es la segunda mitad; la primera es filtrar el
queryset por dueño (ver `core.api.base_views.PorDuenoMixin`). Hacen falta las
dos: el permiso protege el acceso directo por id, el filtro evita que el listado
muestre lo ajeno.
"""

from __future__ import annotations

from typing import Any

from django.db.models import Model
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class EsDuenoOAdmin(BasePermission):
    """Solo el dueño del objeto (o el staff) puede verlo o modificarlo."""

    message = "Este recurso no te pertenece."
    campo_dueno = "usuario"

    def has_object_permission(self, request: Request, view: APIView, obj: Model) -> bool:
        if request.user.is_staff:
            return True

        campo = getattr(view, "campo_dueno", self.campo_dueno)
        return getattr(obj, campo, None) == request.user


class EsAdminOSoloLectura(BasePermission):
    """Cualquiera puede leer; solo el staff puede escribir.

    Es lo que corresponde al catálogo: los productos se muestran a visitantes sin
    cuenta, pero crearlos, cambiarles el precio o borrarlos es tarea de la dueña
    de la tienda. Antes bastaba con `IsAuthenticated`, así que cualquier cliente
    registrado podía editar precios y stock.
    """

    message = "Solo la administración de la tienda puede modificar esto."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class EsAutorOSoloLectura(BasePermission):
    """Las reseñas se leen públicamente, pero cada quien solo edita la suya."""

    message = "Solo puedes modificar tus propias reseñas."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        return obj.usuario == request.user

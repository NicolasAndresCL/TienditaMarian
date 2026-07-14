"""Vistas base de la API.

ADR-001 — Se mantiene `GenericAPIView` + mixins, no se migra a ViewSets + router
------------------------------------------------------------------------------
Decisión del cliente. La API tiene endpoints que no son CRUD y no calzan en el
router de un ViewSet (`carrito/add`, `carrito/update-cantidad`, `carrito/clear`,
`checkout`), y prefiere el control explícito de una clase por operación antes que
las acciones extra de un router.

Lo que sí había que arreglar era la **duplicación**: siete apps repetían el mismo
bloque, copiado a mano una y otra vez:

    class LoQueSea(mixins.ListModelMixin, mixins.CreateModelMixin, GenericAPIView):
        def get(self, request, *args, **kwargs):
            return self.list(request)          # además perdía *args/**kwargs
        def post(self, request, *args, **kwargs):
            return self.create(request)

Aquí ese cableado se escribe una vez. Cada app hereda y declara solo lo suyo:
`queryset`, `serializer_class` y `permission_classes`.
"""

from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response


class BaseListCreateView(mixins.ListModelMixin, mixins.CreateModelMixin, GenericAPIView):
    """GET lista (paginada) · POST crea."""

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.list(request, *args, **kwargs)

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.create(request, *args, **kwargs)


class BaseRetrieveUpdateDestroyView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericAPIView,
):
    """GET detalle · PUT reemplaza · PATCH actualiza parcial · DELETE elimina."""

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.retrieve(request, *args, **kwargs)

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.update(request, *args, **kwargs)

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.destroy(request, *args, **kwargs)


class PorDuenoMixin:
    """Restringe la vista a los objetos del usuario autenticado.

    Es la otra mitad de `EsDuenoOAdmin`: el permiso protege el acceso directo por
    id, y este filtro evita que el **listado** muestre lo ajeno. Sin él, un GET a
    la colección seguiría devolviendo los datos de todos los clientes aunque el
    detalle estuviera protegido.

    `perform_create` fuerza el dueño desde `request.user` y **nunca** desde el
    cuerpo de la petición: así no se puede crear un pago o una reseña a nombre de
    otra persona mandando `{"usuario": 7}`.
    """

    campo_dueno: str = "usuario"

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        usuario = self.request.user

        if usuario.is_staff:
            return queryset

        return queryset.filter(**{self.campo_dueno: usuario})

    def perform_create(self, serializer) -> None:
        serializer.save(**{self.campo_dueno: self.request.user})

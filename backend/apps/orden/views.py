"""Vistas de órdenes: el historial de compras de la usuaria."""

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.orden.selectors import filtrar_ordenes, ordenes_de
from apps.orden.serializers import OrdenSerializer
from core.api.permissions import EsDuenoOAdmin


@extend_schema_view(
    get=extend_schema(
        operation_id="orden.list",
        tags=["Órdenes"],
        summary="Historial de órdenes",
        description="Órdenes del usuario autenticado. Filtrable por fecha y estado de pago.",
        parameters=[
            OpenApiParameter(
                name="fecha_inicio",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filtrar desde esta fecha (YYYY-MM-DD), inclusive.",
            ),
            OpenApiParameter(
                name="fecha_fin",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filtrar hasta esta fecha (YYYY-MM-DD), inclusive.",
            ),
            OpenApiParameter(
                name="pagado",
                type=str,
                location=OpenApiParameter.QUERY,
                description="true / false. Si se omite, no filtra.",
            ),
        ],
        responses={200: OrdenSerializer(many=True)},
    )
)
class OrdenListView(mixins.ListModelMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrdenSerializer

    def get_queryset(self):
        # Los filtros y sus casos límite viven en el selector; la vista solo pasa
        # los parámetros. La paginación la aplica el ListModelMixin con la clase
        # global, en vez de instanciar un paginador a mano en cada petición.
        return filtrar_ordenes(
            self.request.user,
            fecha_inicio=self.request.query_params.get("fecha_inicio"),
            fecha_fin=self.request.query_params.get("fecha_fin"),
            pagado=self.request.query_params.get("pagado"),
        )

    def get(self, request: Request, *args, **kwargs) -> Response:
        return self.list(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="orden.detail",
        tags=["Órdenes"],
        summary="Detalle de una orden",
        responses={200: OrdenSerializer, 404: OpenApiResponse(description="No encontrada.")},
    )
)
class OrdenDetailView(mixins.RetrieveModelMixin, GenericAPIView):
    permission_classes = [IsAuthenticated, EsDuenoOAdmin]
    serializer_class = OrdenSerializer

    def get_queryset(self):
        return ordenes_de(self.request.user)

    def get(self, request: Request, *args, **kwargs) -> Response:
        return self.retrieve(request, *args, **kwargs)

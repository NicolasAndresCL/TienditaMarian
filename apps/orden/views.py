from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination

from apps.orden.models import Orden
from apps.orden.serializers import OrdenSerializer
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiResponse

@extend_schema_view(
    get=extend_schema(
        operation_id="orden.list",
        tags=["Órdenes"],
        summary="Historial de órdenes",
        description="Retorna las órdenes del usuario autenticado. Filtrable por fecha y estado de pago.",
        parameters=[
            OpenApiParameter(name="fecha_inicio", type=str, location=OpenApiParameter.QUERY, description="Filtrar desde esta fecha (YYYY-MM-DD)"),
            OpenApiParameter(name="fecha_fin", type=str, location=OpenApiParameter.QUERY, description="Filtrar hasta esta fecha (YYYY-MM-DD)"),
            OpenApiParameter(name="pagado", type=str, location=OpenApiParameter.QUERY, description="Filtrar por pago: true / false")
        ],
        responses={200: OrdenSerializer(many=True)}
    )
)
class OrdenListView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrdenSerializer
    pagination_class = PageNumberPagination

    def get(self, request):
        ordenes = Orden.objects.filter(usuario=request.user).order_by('-creado')
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        pagado = request.query_params.get('pagado')

        if fecha_inicio:
            ordenes = ordenes.filter(creado__gte=fecha_inicio)
        if fecha_fin:
            ordenes = ordenes.filter(creado__lte=fecha_fin)
        if pagado is not None:
            ordenes = ordenes.filter(pagado=pagado.lower() in ['true', '1'])

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(ordenes, request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        operation_id="orden.detail",
        tags=["Órdenes"],
        summary="Detalle de una orden",
        description="Devuelve la información completa de una orden específica del usuario.",
        responses={
            200: OrdenSerializer,
            404: OpenApiResponse(description="Orden no encontrada.")
        }
    )
)
class OrdenDetailView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrdenSerializer

    def get(self, request, pk):
        orden = get_object_or_404(Orden, pk=pk, usuario=request.user)
        serializer = self.get_serializer(orden)
        return Response(serializer.data)

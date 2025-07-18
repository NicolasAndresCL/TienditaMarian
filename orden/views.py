from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import get_object_or_404

from orden.serializers import Orden, OrdenSerializer
from orden.models import Orden
from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiExample, OpenApiResponse
)

@extend_schema_view(
    get=extend_schema(
        tags=["Ordenes"],
        summary="Historial de órdenes del usuario",
        responses={200: OrdenSerializer(many=True)}
    )
)
class OrdenListView(APIView):
    permission_classes = [IsAuthenticated]
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
        serializer = OrdenSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

@extend_schema_view(
    get=extend_schema(
        tags=["Ordenes"],
        summary="Detalle de una orden",
        responses={200: OrdenSerializer}
    )
)
class OrdenDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        orden = get_object_or_404(Orden, pk=pk, usuario=request.user)
        serializer = OrdenSerializer(orden)
        return Response(serializer.data)
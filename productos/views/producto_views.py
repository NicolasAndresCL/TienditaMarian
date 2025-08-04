from rest_framework.generics import GenericAPIView
from rest_framework import mixins, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from productos.models import Producto
from productos.serializers.producto_serializers import ProductoSerializer
from drf_spectacular.utils import (
    extend_schema_view, extend_schema,
    OpenApiResponse
)

@extend_schema_view(
    get=extend_schema(
        operation_id="producto.list",
        tags=["Productos"],
        summary="Listar productos",
        description="Devuelve una lista paginada de productos disponibles.",
        responses={200: ProductoSerializer(many=True)}
    )
)
class ProductoListView(mixins.ListModelMixin, GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductoSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Producto.objects.all().order_by('-creado')

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

@extend_schema_view(
    post=extend_schema(
        operation_id="producto.create",
        tags=["Productos"],
        summary="Crear producto",
        description="Crea un nuevo producto.",
        responses={201: ProductoSerializer}
    )
)
class ProductoCreateView(mixins.CreateModelMixin, GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductoSerializer

    def get_queryset(self):
        return Producto.objects.all()

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

@extend_schema_view(
    get=extend_schema(
        operation_id="producto.detail",
        tags=["Productos"],
        summary="Detalle de producto",
        description="Obtiene los detalles de un producto por ID.",
        responses={
            200: ProductoSerializer,
            404: OpenApiResponse(description="Producto no encontrado.")
        }
    )
)
class ProductoDetailView(mixins.RetrieveModelMixin, GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductoSerializer

    def get_queryset(self):
        return Producto.objects.all()

    def get(self, request, pk):
        producto = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(producto)
        return Response(serializer.data)

@extend_schema_view(
    put=extend_schema(
        operation_id="producto.update",
        tags=["Productos"],
        summary="Actualizar producto",
        description="Actualiza todos los campos de un producto.",
        responses={200: ProductoSerializer}
    )
)
class ProductoUpdateView(mixins.UpdateModelMixin, GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductoSerializer

    def get_queryset(self):
        return Producto.objects.all()

    def put(self, request, pk, *args, **kwargs):
        return self.update(request, *args, **kwargs)

@extend_schema_view(
    patch=extend_schema(
        operation_id="producto.partial_update",
        tags=["Productos"],
        summary="Actualizar parcialmente producto",
        description="Actualiza campos específicos del producto.",
        responses={200: ProductoSerializer}
    )
)
class ProductoPartialUpdateView(mixins.UpdateModelMixin, GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductoSerializer

    def get_queryset(self):
        return Producto.objects.all()

    def patch(self, request, pk, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

@extend_schema_view(
    delete=extend_schema(
        operation_id="producto.delete",
        tags=["Productos"],
        summary="Eliminar producto",
        description="Elimina un producto específico.",
        responses={
            204: OpenApiResponse(description="Producto eliminado exitosamente."),
            404: OpenApiResponse(description="Producto no encontrado.")
        }
    )
)
class ProductoDeleteView(mixins.DestroyModelMixin, GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductoSerializer

    def get_queryset(self):
        return Producto.objects.all()

    def delete(self, request, pk, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

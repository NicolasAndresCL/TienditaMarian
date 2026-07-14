"""Vistas del catálogo de productos.

Antes, crear, editar y borrar productos solo exigía `IsAuthenticated`: cualquier
cliente que se registrara en la tienda podía cambiar precios, alterar el stock o
borrar el catálogo entero. El catálogo es de la dueña de la tienda, así que las
escrituras pasan a `EsAdminOSoloLectura`; la lectura sigue siendo pública, que es
lo que necesita la vitrina.

Las seis clases originales repetían a mano el mismo `def get/post/put/...`
delegando en los mixins. Ese cableado vive ahora en `core/api/base_views.py`
(ADR-001: se mantiene GenericAPIView + mixins, sin router).
"""

from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from apps.productos.models import Producto
from apps.productos.serializers.producto_serializers import ProductoSerializer
from core.api.permissions import EsAdminOSoloLectura


class ProductoBaseView(GenericAPIView):
    """Todo lo que comparten las vistas del catálogo."""

    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [EsAdminOSoloLectura]


@extend_schema_view(
    get=extend_schema(
        operation_id="producto.list",
        tags=["Productos"],
        summary="Listar productos",
        description="Lista paginada del catálogo. Acceso público.",
        responses={200: ProductoSerializer(many=True)},
    )
)
class ProductoListView(mixins.ListModelMixin, ProductoBaseView):
    def get(self, request: Request, *args, **kwargs) -> Response:
        return self.list(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        operation_id="producto.detail",
        tags=["Productos"],
        summary="Detalle de producto",
        description="Obtiene un producto por su id. Acceso público.",
        responses={200: ProductoSerializer, 404: OpenApiResponse(description="No encontrado.")},
    )
)
class ProductoDetailView(mixins.RetrieveModelMixin, ProductoBaseView):
    def get(self, request: Request, *args, **kwargs) -> Response:
        return self.retrieve(request, *args, **kwargs)


@extend_schema_view(
    post=extend_schema(
        operation_id="producto.create",
        tags=["Productos"],
        summary="Crear producto",
        description="Solo la administración de la tienda.",
        responses={201: ProductoSerializer},
    )
)
class ProductoCreateView(mixins.CreateModelMixin, ProductoBaseView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        return self.create(request, *args, **kwargs)


@extend_schema_view(
    put=extend_schema(
        operation_id="producto.update",
        tags=["Productos"],
        summary="Actualizar producto",
        description="Solo la administración de la tienda.",
        responses={200: ProductoSerializer},
    )
)
class ProductoUpdateView(mixins.UpdateModelMixin, ProductoBaseView):
    def put(self, request: Request, *args, **kwargs) -> Response:
        return self.update(request, *args, **kwargs)


@extend_schema_view(
    patch=extend_schema(
        operation_id="producto.partial_update",
        tags=["Productos"],
        summary="Actualizar producto parcialmente",
        description="Solo la administración de la tienda.",
        responses={200: ProductoSerializer},
    )
)
class ProductoPartialUpdateView(mixins.UpdateModelMixin, ProductoBaseView):
    def patch(self, request: Request, *args, **kwargs) -> Response:
        return self.partial_update(request, *args, **kwargs)


@extend_schema_view(
    delete=extend_schema(
        operation_id="producto.delete",
        tags=["Productos"],
        summary="Eliminar producto",
        description="Solo la administración de la tienda.",
        responses={
            204: OpenApiResponse(description="Producto eliminado."),
            404: OpenApiResponse(description="No encontrado."),
        },
    )
)
class ProductoDeleteView(mixins.DestroyModelMixin, ProductoBaseView):
    def delete(self, request: Request, *args, **kwargs) -> Response:
        return self.destroy(request, *args, **kwargs)

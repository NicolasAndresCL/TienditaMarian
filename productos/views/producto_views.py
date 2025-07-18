from productos.models import Producto
from productos.serializers.producto_serializers import ProductoSerializer
from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    list=extend_schema(tags=["Productos"]),
    retrieve=extend_schema(tags=["Productos"]),
    create=extend_schema(tags=["Productos"]),
    update=extend_schema(tags=["Productos"]),
    partial_update=extend_schema(tags=["Productos"]),
    destroy=extend_schema(tags=["Productos"]),
)

class ProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Producto.objects.all().order_by('-creado')
    serializer_class = ProductoSerializer

    def get_serializer_context(self):
        return {"request": self.request}

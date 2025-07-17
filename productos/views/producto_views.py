from productos.models import Producto
from productos.serializers.producto_serializers import ProductoSerializer
from rest_framework import viewsets, permissions

class ProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Producto.objects.all().order_by('-creado')
    serializer_class = ProductoSerializer

    def get_serializer_context(self):
        return {"request": self.request}

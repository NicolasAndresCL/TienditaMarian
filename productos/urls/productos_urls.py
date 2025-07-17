from django.urls import path
from productos.views.producto_views import ProductoViewSet

urlpatterns = [
    path('listar/', ProductoViewSet.as_view({'get': 'list'}), name='listar-productos'),
    # otras rutas de productos
]

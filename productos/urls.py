from django.urls import path
from django.urls import include
from productos.views.producto_views import ProductoViewSet

from productos.views.home_view import home


urlpatterns = [
    path('',  home, name='home'),
    path('', include('productos.carrito_urls')),
    path('productos/', ProductoViewSet.as_view({'get': 'list'}), name='producto-list'),
]

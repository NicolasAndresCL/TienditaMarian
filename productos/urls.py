from django.urls import path
from django.urls import include
from . import views


urlpatterns = [
    path('',  views.home, name='home'),
    # ...otras rutas...
    path('', include('productos.carrito_urls')),
]

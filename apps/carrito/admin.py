from django.contrib import admin
from apps.carrito.models import Carrito, ItemCarrito

admin.site.register(Carrito)
admin.site.register(ItemCarrito)
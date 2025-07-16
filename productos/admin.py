from django.contrib import admin
from .models import Producto  # o el nombre de tu modelo

admin.site.register(Producto)
from .carrito_models import Carrito, ItemCarrito, Orden, ItemOrden

admin.site.register(Carrito)
admin.site.register(ItemCarrito)
admin.site.register(Orden)
admin.site.register(ItemOrden)


from django.contrib import admin
from productos.models import Producto
from productos.carrito_models import Carrito, ItemCarrito, Orden, ItemOrden

admin.site.register(Producto)
admin.site.register(Carrito)
admin.site.register(ItemCarrito)
admin.site.register(Orden)
admin.site.register(ItemOrden)

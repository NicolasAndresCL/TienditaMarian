from django.contrib import admin
from apps.orden.models import  Orden, ItemOrden

admin.site.register(Orden)
admin.site.register(ItemOrden)

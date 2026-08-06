from django.contrib import admin

from apps.orden.models import ItemOrden, Orden

admin.site.register(Orden)
admin.site.register(ItemOrden)

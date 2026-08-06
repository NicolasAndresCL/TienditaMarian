from decimal import Decimal

from rest_framework import serializers

from apps.orden.models import ItemOrden, Orden
from apps.productos.serializers.producto_serializers import ProductoSimpleSerializer


class ItemOrdenSerializer(serializers.ModelSerializer):
    # El import de ProductoSimpleSerializer estaba DENTRO del cuerpo de la clase
    # para esquivar un ciclo con `apps.carrito`. Al mover el serializer a la app
    # de productos —que es donde corresponde— el ciclo desaparece y el import
    # vuelve arriba, como cualquier otro.
    producto = ProductoSimpleSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = ItemOrden
        fields = ['id', 'producto', 'cantidad', 'precio', 'subtotal']

    def get_subtotal(self, item: ItemOrden) -> Decimal:
        return item.subtotal


class OrdenSerializer(serializers.ModelSerializer):
    items = ItemOrdenSerializer(many=True, read_only=True)
    usuario = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Orden
        fields = ['id', 'usuario', 'creado', 'estado', 'total', 'pagado', 'items']
        read_only_fields = ['id', 'usuario', 'creado', 'estado', 'total', 'pagado', 'items']

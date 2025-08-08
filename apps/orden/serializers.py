from rest_framework import serializers
from apps.orden.models import  Orden, ItemOrden

class ItemOrdenSerializer(serializers.ModelSerializer):
    from apps.carrito.serializers import ProductoSimpleSerializer
    producto = ProductoSimpleSerializer(read_only=True)

    class Meta:
        model = ItemOrden
        fields = ['id', 'producto', 'cantidad', 'precio']

class OrdenSerializer(serializers.ModelSerializer):
    items = ItemOrdenSerializer(many=True, read_only=True)

    class Meta:
        model = Orden
        fields = ['id', 'usuario', 'creado', 'total', 'pagado', 'items']
        read_only_fields = ['usuario', 'creado', 'total', 'pagado', 'items']

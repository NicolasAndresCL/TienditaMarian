from rest_framework import serializers
from orden.models import  Orden, ItemOrden

class ItemOrdenSerializer(serializers.ModelSerializer):
    from carrito.serializers import ProductoSimpleSerializer
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

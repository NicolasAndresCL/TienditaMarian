from rest_framework import serializers
from carrito.models import Carrito, ItemCarrito
from productos.models import Producto

class ProductoSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'precio']  # Puedes agregar más si lo necesitas

class ItemCarritoSerializer(serializers.ModelSerializer):
    producto = ProductoSimpleSerializer(read_only=True)

    class Meta:
        model = ItemCarrito
        fields = ['id', 'producto', 'cantidad', 'agregado']

class CarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)
    usuario = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Carrito
        fields = ['id', 'usuario', 'creado', 'actualizado', 'items']

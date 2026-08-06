from decimal import Decimal

from rest_framework import serializers

from apps.carrito.models import Carrito, ItemCarrito
from apps.productos.serializers.producto_serializers import ProductoSimpleSerializer


class ItemCarritoSerializer(serializers.ModelSerializer):
    producto = ProductoSimpleSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = ItemCarrito
        fields = ['id', 'producto', 'cantidad', 'subtotal', 'agregado']

    def get_subtotal(self, item: ItemCarrito) -> Decimal:
        return item.producto.precio * item.cantidad


class CarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)
    usuario = serializers.StringRelatedField(read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Carrito
        fields = ['id', 'usuario', 'creado', 'actualizado', 'items', 'total']

    def get_total(self, carrito: Carrito) -> Decimal:
        # El frontend tenía que sumar esto por su cuenta; ahora viene calculado.
        return sum(
            (item.producto.precio * item.cantidad for item in carrito.items.all()),
            Decimal("0.00"),
        )

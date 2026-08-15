from decimal import Decimal

from rest_framework import serializers

from apps.carrito.models import Carrito, ItemCarrito
from apps.productos.serializers.producto_serializers import ProductoSimpleSerializer

# --------------------------------------------------------------- peticiones
#
# Estos tres vivían dentro de `views.py` y, peor, **no se usaban**: las vistas
# declaraban `serializer_class` y luego leían `request.data.get(...)` en crudo,
# así que el serializer solo servía para pintar el esquema de OpenAPI. El
# contrato estaba escrito en dos sitios y solo se cumplía en uno — el servicio,
# que reparseaba a mano lo que aquí ya estaba declarado.


class AgregarItemSerializer(serializers.Serializer):
    """Cuerpo de `POST /carrito/items/`."""

    producto_id = serializers.IntegerField()
    # `min_value=1` cubre el 0 y los negativos; `IntegerField` rechaza "abc" y
    # 2.5. Es la misma regla que `parsear_cantidad` aplica en el servicio, que se
    # conserva como segunda capa para las llamadas internas.
    cantidad = serializers.IntegerField(required=False, default=1, min_value=1)


class ActualizarCantidadSerializer(serializers.Serializer):
    """Cuerpo de `PATCH /carrito/items/cantidad/`.

    Aquí `cantidad` es **obligatoria**, al contrario que al agregar. Antes se
    reutilizaba el serializer de agregar, con su `default=1`: un PATCH sin
    cantidad dejaba el ítem en 1 unidad sin que nadie lo hubiera pedido.
    """

    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)


class QuitarItemSerializer(serializers.Serializer):
    """Cuerpo de `DELETE /carrito/items/quitar/`."""

    producto_id = serializers.IntegerField()


class CheckoutSerializer(serializers.Serializer):
    """Cuerpo de `POST /checkout/`."""

    cupon = serializers.CharField(required=False, allow_blank=True)


# ----------------------------------------------------------------- respuestas


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

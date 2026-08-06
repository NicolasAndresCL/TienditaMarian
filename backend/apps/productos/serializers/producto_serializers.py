from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.productos.models import Producto


class ProductoSimpleSerializer(serializers.ModelSerializer):
    """Vista mínima de un producto, para anidar en carritos y órdenes.

    Vivía en `apps/carrito/serializers.py` y desde ahí lo importaba `orden`, que
    para esquivar el import circular tenía que hacer el import **dentro del
    cuerpo de la clase**. Un producto no es parte del dominio del carrito: su
    serializer pertenece a `productos`, y con eso el ciclo desaparece.
    """

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'precio']


class ProductoSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'image', 'precio', 'stock', 'creado']
        read_only_fields = ['id', 'creado']

    @extend_schema_field(str)
    def get_image(self, obj: Producto) -> str | None:
        if not obj.image:
            return None

        request = self.context.get('request')
        # Sin `request` en el contexto (por ejemplo, al serializar desde un
        # comando o un test) esto era un AttributeError: `None.build_absolute_uri`.
        if request is None:
            return obj.image.url

        return request.build_absolute_uri(obj.image.url)

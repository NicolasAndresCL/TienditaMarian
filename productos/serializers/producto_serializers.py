from rest_framework import serializers
from productos.models import Producto
from drf_spectacular.utils import extend_schema_field

class ProductoSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = '__all__'

    @extend_schema_field(str)
    def get_image(self, obj) -> str:
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

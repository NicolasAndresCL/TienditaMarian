# productos/serializers.py
from rest_framework import serializers
from .models import Producto

class ProductoSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField() # ¡CAMBIADO A 'image'!

    class Meta:
        model = Producto
        fields = '__all__'

    def get_image(self, obj): # ¡CAMBIADO A 'get_image'!
        request = self.context.get('request')
        if obj.image: # ¡CAMBIADO A 'obj.image'!
            return request.build_absolute_uri(obj.image.url)
        return None
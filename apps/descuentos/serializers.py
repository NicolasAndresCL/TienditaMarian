from rest_framework import serializers
from .models import Descuento

class DescuentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Descuento
        fields = '__all__'
        read_only_fields = ['id']

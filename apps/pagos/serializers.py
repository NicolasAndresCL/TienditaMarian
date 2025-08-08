from rest_framework import serializers
from .models import Pago

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'
        read_only_fields = ['fecha_pago']

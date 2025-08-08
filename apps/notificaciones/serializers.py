from rest_framework import serializers
from .models import Notificacion

class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = '__all__'
        read_only_fields = ['fecha_creacion']

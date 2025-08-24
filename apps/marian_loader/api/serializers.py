from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.marian_loader.models import HitoCarga, DetalleCarga

User = get_user_model()


class FileUploadSerializer(serializers.Serializer):
    """
    Serializer para recibir el CSV desde la petición multipart/form-data.
    """
    archivo = serializers.FileField(
        help_text="Archivo CSV con los productos a importar"
    )


class DetalleCargaSerializer(serializers.ModelSerializer):
    """
    Serializer de salida para cada fila procesada en un HitoCarga.
    """
    producto_id = serializers.IntegerField(
        source='producto.id',
        read_only=True
    )
    producto_sku = serializers.CharField(
        source='producto.sku',
        read_only=True
    )

    class Meta:
        model = DetalleCarga
        fields = [
            'fila',
            'datos',
            'errores',
            'producto_id',
            'producto_sku',
        ]


class HitoCargaSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar el estado y resultado de una carga.
    Incluye detalles de cada fila.
    """
    usuario = serializers.StringRelatedField(read_only=True)
    detalles = DetalleCargaSerializer(many=True, read_only=True)

    class Meta:
        model = HitoCarga
        fields = [
            'id',
            'usuario',
            'fecha_inicio',
            'fecha_fin',
            'total',
            'exitosos',
            'fallidos',
            'archivo',
            'status',
            'reporte',
            'detalles',
        ]
        read_only_fields = fields


class HitoCargaCreateSerializer(FileUploadSerializer):
    """
    Extiende FileUploadSerializer para documentar mejor el endpoint de creación.
    No expone campos de HitoCarga; devuelve HitoCargaSerializer en la vista.
    """
    pass

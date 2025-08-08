from django.db import models
from django.contrib.auth import get_user_model
from apps.orden.models import Orden

User = get_user_model()

class Envio(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('fallido', 'Fallido'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='envios')
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='envios')
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=20)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_envio = models.DateTimeField(auto_now_add=True)
    tracking_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'Envio {self.id} - {self.estado}'

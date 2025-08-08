from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Descuento(models.Model):
    TIPO_CHOICES = [
        ('porcentaje', 'Porcentaje'),
        ('fijo', 'Monto fijo'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='descuentos_personalizados')

    def __str__(self):
        return f'{self.nombre} ({self.tipo} - {self.valor:.2f})'

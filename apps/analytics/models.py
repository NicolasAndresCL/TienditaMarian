from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AnalyticsEvent(models.Model):
    EVENT_TYPES = [
        ('view', 'Vista de producto'),
        ('search', 'Búsqueda'),
        ('purchase', 'Compra'),
        ('login', 'Inicio de sesión'),
        ('custom', 'Evento personalizado'),
    ]

    tipo_evento = models.CharField(max_length=20, choices=EVENT_TYPES)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.tipo_evento} - {self.timestamp.strftime("%Y-%m-%d %H:%M:%S")}'

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('email', 'Email'),
        ('alerta', 'Alerta interna'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    asunto = models.CharField(max_length=255)
    mensaje = models.TextField()
    enviada = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notificación {self.id} - {self.tipo} - {"Enviada" if self.enviada else "Pendiente"}'

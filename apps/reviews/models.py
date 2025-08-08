from django.db import models
from django.contrib.auth import get_user_model
from apps.productos.models import Producto

User = get_user_model()

class Review(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='reviews')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    comentario = models.TextField()
    calificacion = models.PositiveSmallIntegerField()  # 1 a 5
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review {self.id} - {self.calificacion}⭐'

from django.db import models
from django.conf import settings
from apps.productos.models import Producto

class Carrito(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carrito')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('carrito', 'producto')

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
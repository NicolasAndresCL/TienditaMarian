
from django.db import models


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    image = models.ImageField(upload_to='productos/images/', blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Sin un orden explícito la paginación es inestable: la misma
        # página puede devolver filas distintas entre dos peticiones.
        ordering = ['-creado']
        verbose_name_plural = 'Productos'

    def __str__(self):
        return self.nombre
    

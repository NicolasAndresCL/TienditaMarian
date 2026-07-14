
from django.contrib.auth import get_user_model
from django.db import models

from apps.orden.models import Orden

User = get_user_model()

class Pago(models.Model):
    METODO_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('webpay', 'Webpay'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pagos')
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES)
    estado = models.CharField(max_length=20, default='pendiente')  # pagado, fallido, pendiente
    fecha_pago = models.DateTimeField(auto_now_add=True)
    # Sin `null=True`: evita tener NULL y '' como dos representaciones de "vacío".
    transaccion_id = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        # Sin un orden explícito la paginación es inestable: la misma
        # página puede devolver filas distintas entre dos peticiones.
        ordering = ['-fecha_pago']
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f'Pago {self.id} - {self.metodo} - {self.estado}'

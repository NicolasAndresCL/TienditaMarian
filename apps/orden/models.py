from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
from apps.productos.models import Producto

class Orden(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ordenes',
        verbose_name=_("Usuario")
    )
    creado = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de creación"))
    actualizado = models.DateTimeField(auto_now=True, verbose_name=_("Última actualización"))
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Total"))
    pagado = models.BooleanField(default=False, verbose_name=_("¿Pagado?"))

    class Meta:
        verbose_name = _("Orden")
        verbose_name_plural = _("Órdenes")
        ordering = ['-creado']

    def __str__(self) -> str:
        return f"Orden #{self.id} de {self.usuario.username}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            send_mail(
                subject="Gracias por tu compra",
                message=f"Hola {self.usuario.username}, tu orden #{self.id} ha sido registrada.",
                from_email="no-reply@tiendita.com",
                recipient_list=[self.usuario.email],
                fail_silently=True,
            )


class ItemOrden(models.Model):
    orden = models.ForeignKey(
        Orden,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Orden")
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        verbose_name=_("Producto")
    )
    cantidad = models.PositiveIntegerField(verbose_name=_("Cantidad"))
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Precio unitario"))

    class Meta:
        verbose_name = _("Ítem de orden")
        verbose_name_plural = _("Ítems de orden")

    def __str__(self) -> str:
        return f"{self.cantidad} x {self.producto.nombre}"

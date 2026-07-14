from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.productos.models import Producto

ESTADOS = [
    ('pendiente', 'Pendiente'),
    ('enviado', 'Enviado'),
    ('entregado', 'Entregado'),
]


class Orden(models.Model):
    """Una compra confirmada.

    El modelo ya NO manda correos. Antes `save()` llamaba a `send_mail()`, con
    dos consecuencias: la clienta recibía el mensaje duplicado (la señal
    post_save enviaba otro igual), y el correo salía **dentro** de la transacción
    del checkout — si esta se revertía, quedaba un "gracias por tu compra" de una
    orden que nunca llegó a existir.

    Ahora los efectos posteriores viven en `apps/orden/subscribers.py` y se
    disparan por evento, después del commit.
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ordenes',
        verbose_name=_("Usuario"),
    )
    creado = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de creación"))
    actualizado = models.DateTimeField(auto_now=True, verbose_name=_("Última actualización"))
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Total"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    pagado = models.BooleanField(default=False, verbose_name=_("¿Pagado?"))

    class Meta:
        verbose_name = _("Orden")
        verbose_name_plural = _("Órdenes")
        ordering = ['-creado']
        indexes = [
            # El historial siempre se consulta así: "las órdenes de esta usuaria,
            # de la más nueva a la más vieja".
            models.Index(fields=["usuario", "-creado"], name="orden_usuario_creado_idx"),
        ]

    def __str__(self) -> str:
        return f"Orden #{self.id} de {self.usuario.username}"


class ItemOrden(models.Model):
    orden = models.ForeignKey(
        Orden,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Orden"),
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        verbose_name=_("Producto"),
    )
    cantidad = models.PositiveIntegerField(verbose_name=_("Cantidad"))
    # El precio se congela al comprar: si mañana sube, esta orden conserva el
    # precio que la clienta pagó.
    precio = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Precio unitario")
    )

    class Meta:
        verbose_name = _("Ítem de orden")
        verbose_name_plural = _("Ítems de orden")
        ordering = ['id']

    def __str__(self) -> str:
        return f"{self.cantidad} x {self.producto.nombre}"

    @property
    def subtotal(self) -> Decimal:
        return self.precio * self.cantidad

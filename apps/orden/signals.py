"""Señales de órdenes.

OJO — deuda conocida: este `send_mail` está duplicado con el que hace
`Orden.save()`, así que hoy el cliente recibe **dos** correos idénticos por
compra. El test de caracterización `test_crear_orden_envia_dos_correos_bug_conocido`
congela esa conducta. La Fase 3 elimina el envío desde el modelo y deja este
como única fuente.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Orden

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Orden)
def enviar_email_nueva_orden(sender, instance, created, **kwargs):
    if not created:
        return

    usuario = instance.usuario
    if not usuario.email:
        logger.info("Orden %s sin correo de destino; no se notifica.", instance.pk)
        return

    try:
        send_mail(
            subject='¡Gracias por tu compra!',
            message=f'Se ha creado tu orden #{instance.id} por un total de ${instance.total}.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            fail_silently=True,
        )
    except Exception:
        # `logger.exception` deja el traceback completo; el `print` anterior se
        # perdía en la salida estándar del servidor.
        logger.exception("Falló el correo de confirmación de la orden %s", instance.pk)

"""Efectos posteriores a una orden, declarados de forma explícita.

Antes esto estaba repartido en tres sitios invisibles desde el checkout:

    Orden.save()                  → send_mail(...)   ← un modelo mandando correos
    apps/orden/signals.py         → send_mail(...)   ← el MISMO correo otra vez
    apps/notificaciones/signals.py→ Notificacion(...)

De ahí salían los dos correos idénticos por compra. Además, `Orden.save()`
enviaba el correo dentro de la transacción del checkout: si la transacción se
revertía, la clienta ya había recibido el "gracias por tu compra" de una orden
que nunca existió.

Ahora cada efecto es una función suscrita a un evento. Se leen de un vistazo, se
prueban una por una y ninguna puede tumbar la venta: el despachador aísla los
fallos (skill §2.2).
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

from apps.envios.models import Envio
from apps.notificaciones.models import Notificacion
from apps.orden.models import Orden
from core.events import Evento, despachador

logger = logging.getLogger(__name__)


def enviar_correo_confirmacion(orden: Orden) -> None:
    """Un único correo de confirmación por orden."""
    destinatario = orden.usuario.email
    if not destinatario:
        logger.info("La orden %s no tiene correo de destino; no se notifica.", orden.pk)
        return

    send_mail(
        subject="¡Gracias por tu compra!",
        message=(
            f"Hola {orden.usuario.username}, tu orden #{orden.id} quedó registrada "
            f"por un total de ${orden.total}."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destinatario],
    )
    logger.info("Correo de confirmación enviado para la orden %s", orden.pk)


def crear_notificacion(orden: Orden) -> None:
    estado = "Pagada" if orden.pagado else "Pendiente"
    Notificacion.objects.create(
        usuario=orden.usuario,
        tipo="email",
        asunto="Nueva orden creada",
        mensaje=f"Se ha creado la orden #{orden.id} con estado {estado}.",
        enviada=False,
    )


def crear_envio_pendiente(orden: Orden) -> None:
    """Deja el envío listo para que la tienda le complete la dirección.

    El checkout no creaba ningún envío, así que la app `envios` estaba
    desconectada del flujo: las órdenes nacían sin forma de despacharse.
    """
    Envio.objects.create(
        usuario=orden.usuario,
        orden=orden,
        direccion="",
        ciudad="",
        codigo_postal="",
        estado="pendiente",
    )


def enviar_correo_pago(orden: Orden) -> None:
    """Confirma el cobro.

    `ORDEN_PAGADA` se emitía al vacío: el evento existía, `PagoService` lo
    anunciaba y no había nadie suscrito. Una compra pagada no le decía nada a la
    clienta.
    """
    destinatario = orden.usuario.email
    if not destinatario:
        logger.info("La orden %s no tiene correo de destino; no se notifica el pago.", orden.pk)
        return

    send_mail(
        subject="Confirmamos tu pago",
        message=(
            f"Hola {orden.usuario.username}, recibimos el pago de tu orden #{orden.id} "
            f"por ${orden.total}. La estamos preparando."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destinatario],
    )
    logger.info("Correo de pago enviado para la orden %s", orden.pk)


def notificar_pago(orden: Orden) -> None:
    Notificacion.objects.create(
        usuario=orden.usuario,
        tipo="email",
        asunto="Pago recibido",
        mensaje=f"El pago de la orden #{orden.id} fue confirmado.",
        enviada=False,
    )


def registrar_suscriptores() -> None:
    """Conecta los efectos. Se llama una vez, desde `OrdenConfig.ready()`."""
    despachador.suscribir(Evento.ORDEN_CREADA, enviar_correo_confirmacion)
    despachador.suscribir(Evento.ORDEN_CREADA, crear_notificacion)
    despachador.suscribir(Evento.ORDEN_CREADA, crear_envio_pendiente)

    despachador.suscribir(Evento.ORDEN_PAGADA, enviar_correo_pago)
    despachador.suscribir(Evento.ORDEN_PAGADA, notificar_pago)

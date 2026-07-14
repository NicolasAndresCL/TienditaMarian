"""Tests de órdenes."""

import pytest
from django.core import mail

from apps.orden.models import Orden


@pytest.mark.django_db
def test_crear_una_orden_no_manda_correos_por_si_sola(usuario):
    """Antes `Orden.save()` llamaba a `send_mail()`. Ya no: un modelo no notifica.

    Este test cierra el ciclo del de caracterización que congelaba el bug del
    doble correo. Había dos envíos —uno desde `save()` y otro desde la señal
    post_save— y la clienta recibía el mensaje repetido. Peor: el correo del
    modelo salía DENTRO de la transacción del checkout, así que una compra que
    después se revertía igual dejaba enviado un "gracias por tu compra".

    Ahora notificar es un efecto del evento ORDEN_CREADA, que el checkout emite
    tras confirmar la transacción. Que salga exactamente un correo se verifica en
    `apps/carrito/tests/test_checkout.py::test_comprar_manda_un_solo_correo`.
    """
    mail.outbox.clear()

    Orden.objects.create(usuario=usuario, total=1000)

    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_orden_pertenece_al_usuario(usuario):
    orden = Orden.objects.create(usuario=usuario, total=1000)

    assert orden.usuario == usuario
    assert orden.estado == "pendiente"
    assert orden.pagado is False

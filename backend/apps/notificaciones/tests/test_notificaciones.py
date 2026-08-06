"""Tests de notificaciones."""

import pytest

from apps.carrito.models import Carrito, ItemCarrito
from apps.carrito.services import CheckoutService
from apps.notificaciones.models import Notificacion
from apps.orden.models import Orden


@pytest.mark.django_db
def test_crear_notificacion(usuario):
    noti = Notificacion.objects.create(
        usuario=usuario,
        tipo='email',
        asunto='Confirmación de orden',
        mensaje='Tu orden ha sido confirmada.',
        enviada=False,
    )

    assert noti.enviada is False
    assert str(noti) == f'Notificación {noti.id} - email - Pendiente'


@pytest.mark.django_db
def test_guardar_una_orden_no_genera_notificaciones_por_si_solo(usuario):
    """La notificación ya no cuelga de un post_save del modelo.

    Antes, cualquier `Orden.objects.create()` —incluido el de un script o el de
    un test— disparaba una notificación. Ahora es un efecto de **comprar**, no de
    guardar una fila.
    """
    Orden.objects.create(usuario=usuario, total=19000)

    assert Notificacion.objects.filter(usuario=usuario).count() == 0


@pytest.mark.django_db(transaction=True)
def test_comprar_genera_la_notificacion(usuario, producto):
    """El evento ORDEN_CREADA del checkout es el que la produce."""
    carrito = Carrito.objects.create(usuario=usuario)
    ItemCarrito.objects.create(carrito=carrito, producto=producto, cantidad=1)

    CheckoutService(usuario).ejecutar()

    notificaciones = Notificacion.objects.filter(usuario=usuario)
    assert notificaciones.count() == 1
    assert 'Nueva orden creada' in notificaciones.first().asunto

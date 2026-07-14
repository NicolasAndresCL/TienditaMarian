"""Tests de notificaciones."""

import pytest

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
def test_crear_una_orden_genera_su_notificacion(usuario):
    Orden.objects.create(usuario=usuario, estado='pendiente', total=19000)

    notificaciones = Notificacion.objects.filter(usuario=usuario)
    assert notificaciones.count() == 1
    assert 'Nueva orden creada' in notificaciones.first().asunto

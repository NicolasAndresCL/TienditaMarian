"""Tests de órdenes."""

import pytest
from django.core import mail

from apps.orden.models import Orden


@pytest.mark.django_db
def test_crear_orden_envia_dos_correos_bug_conocido(usuario):
    """CARACTERIZACIÓN — fija el comportamiento actual, que está MAL.

    Al crear una orden salen **dos** correos idénticos, porque el envío está
    duplicado en dos lugares: `Orden.save()` manda uno y la señal `post_save`
    de `apps/orden/signals.py` manda otro. El cliente recibe el mensaje repetido.

    El test se deja pasando a propósito (skill §3: nunca un big-bang a ciegas):
    congela la conducta de hoy para que, cuando la Fase 3 saque el `send_mail`
    del modelo, el cambio sea visible y deliberado en el diff en vez de una
    regresión silenciosa. En esa fase este test pasa a exigir **un** correo.
    """
    Orden.objects.create(usuario=usuario, total=1000)

    assert len(mail.outbox) == 2, "si esto cambió, actualiza el test junto con el arreglo"
    assert "Gracias por tu compra" in mail.outbox[0].subject


@pytest.mark.django_db
def test_orden_pertenece_al_usuario(usuario):
    orden = Orden.objects.create(usuario=usuario, total=1000)

    assert orden.usuario == usuario
    assert orden.estado == "pendiente"
    assert orden.pagado is False

"""El endpoint que cobra una orden.

`PagoService` estaba escrito y probado desde hacía tiempo —bloqueo de fila,
idempotencia, emisión de `ORDEN_PAGADA`— y **no lo llamaba nadie salvo los
tests**: `POST /pagos/` solo creaba una fila en estado `pendiente`, sin cobrar ni
tocar la orden. Las órdenes se quedaban en "Pendiente" para siempre y la tienda
no tenía forma de cobrar.

Estos tests cubren el camino HTTP que faltaba.
"""

from decimal import Decimal

import pytest

from apps.notificaciones.models import Notificacion
from apps.orden.models import Orden
from apps.pagos.models import Pago


@pytest.fixture
def orden(db, usuario) -> Orden:
    return Orden.objects.create(usuario=usuario, total=Decimal("6000.00"))


@pytest.mark.django_db
def test_pagar_marca_la_orden_y_registra_el_pago(auth_client, orden):
    respuesta = auth_client.post(f"/api/v1/ordenes/{orden.id}/pagar/", {}, format="json")

    assert respuesta.status_code == 200
    assert respuesta.data["pagado"] is True

    orden.refresh_from_db()
    assert orden.pagado

    pago = Pago.objects.get(orden=orden)
    assert pago.estado == "pagado"
    assert pago.monto == orden.total
    # La pasarela decide el identificador; el cliente no lo manda ni lo elige.
    assert pago.transaccion_id


@pytest.mark.django_db
def test_pagar_dos_veces_no_cobra_dos_veces(auth_client, orden):
    """Idempotencia: un doble clic no puede cobrar dos veces."""
    auth_client.post(f"/api/v1/ordenes/{orden.id}/pagar/", {}, format="json")

    respuesta = auth_client.post(f"/api/v1/ordenes/{orden.id}/pagar/", {}, format="json")

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["codigo"] == "orden_ya_pagada"
    assert Pago.objects.filter(orden=orden).count() == 1


@pytest.mark.django_db
def test_no_se_puede_pagar_la_orden_de_otra_persona(otro_client, orden):
    """Para quien no es la dueña, esa orden no existe: 404, no 403.

    Un 403 confirmaría que la orden existe; el 404 no filtra ni eso.
    """
    respuesta = otro_client.post(f"/api/v1/ordenes/{orden.id}/pagar/", {}, format="json")

    assert respuesta.status_code == 404
    orden.refresh_from_db()
    assert not orden.pagado


@pytest.mark.django_db
def test_un_anonimo_no_puede_pagar(api_client, orden):
    assert api_client.post(f"/api/v1/ordenes/{orden.id}/pagar/", {}, format="json").status_code == 401


@pytest.mark.django_db
def test_pagar_avisa_a_la_clienta(auth_client, orden, mailoutbox, django_capture_on_commit_callbacks):
    """`ORDEN_PAGADA` se emitía al vacío: nadie estaba suscrito.

    Una compra pagada no le decía nada a quien la hizo.

    Hace falta `django_capture_on_commit_callbacks` porque los efectos se emiten
    con `transaction.on_commit` —para que no salga un correo de un pago que
    luego se revierte— y en los tests la transacción no se confirma nunca.
    """
    with django_capture_on_commit_callbacks(execute=True):
        auth_client.post(f"/api/v1/ordenes/{orden.id}/pagar/", {}, format="json")

    assert len(mailoutbox) == 1
    assert "pago" in mailoutbox[0].subject.lower()
    assert Notificacion.objects.filter(usuario=orden.usuario, asunto="Pago recibido").exists()


@pytest.mark.django_db
def test_si_el_pago_se_revierte_no_sale_ningun_correo(auth_client, orden, mailoutbox):
    """El correo va en `on_commit`, así que solo sale si el cobro se confirmó.

    Sin capturar los callbacks, la transacción del test nunca se confirma: es la
    misma situación que un rollback en producción, y la clienta no debe recibir
    un "confirmamos tu pago" de algo que no ocurrió.
    """
    auth_client.post(f"/api/v1/ordenes/{orden.id}/pagar/", {}, format="json")

    assert mailoutbox == []


@pytest.mark.django_db
def test_pagar_una_orden_inexistente_es_404(auth_client):
    assert auth_client.post("/api/v1/ordenes/99999/pagar/", {}, format="json").status_code == 404

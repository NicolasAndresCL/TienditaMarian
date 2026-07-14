"""Tests de pagos."""

from decimal import Decimal

import pytest

from apps.orden.models import Orden
from apps.pagos.models import Pago
from apps.pagos.services import PagoManual, PagoService, PasarelaPago
from core.events import Despachador, Evento
from core.exceptions import OrdenYaPagadaError, PagoRechazadoError


@pytest.fixture
def orden(db, usuario) -> Orden:
    return Orden.objects.create(usuario=usuario, total=Decimal("15000.00"))


@pytest.mark.django_db
def test_un_pago_nace_pendiente(usuario, orden):
    pago = Pago.objects.create(usuario=usuario, orden=orden, monto=orden.total, metodo="webpay")

    assert pago.estado == "pendiente"


@pytest.mark.django_db(transaction=True)
def test_cobrar_marca_la_orden_como_pagada(orden):
    pago = PagoService().cobrar(orden)

    orden.refresh_from_db()
    assert orden.pagado is True
    assert pago.estado == "pagado"
    assert pago.monto == Decimal("15000.00")


@pytest.mark.django_db(transaction=True)
def test_no_se_puede_cobrar_dos_veces_la_misma_orden(orden):
    servicio = PagoService()
    servicio.cobrar(orden)

    with pytest.raises(OrdenYaPagadaError):
        servicio.cobrar(orden)

    assert Pago.objects.filter(orden=orden).count() == 1


@pytest.mark.django_db(transaction=True)
def test_cobrar_emite_el_evento_orden_pagada(orden):
    despachador = Despachador()
    recibidas = []
    despachador.suscribir(Evento.ORDEN_PAGADA, recibidas.append)

    PagoService(despachador=despachador).cobrar(orden)

    assert recibidas == [orden]


@pytest.mark.django_db(transaction=True)
def test_una_pasarela_puede_rechazar_el_cobro(orden):
    """La interfaz permite enchufar Webpay o Stripe sin tocar el dominio."""

    class PasarelaQueRechaza(PasarelaPago):
        nombre = "webpay"

        def cobrar(self, orden, monto):
            raise PagoRechazadoError("fondos insuficientes", monto)

    with pytest.raises(PagoRechazadoError):
        PagoService(pasarela=PasarelaQueRechaza()).cobrar(orden)

    orden.refresh_from_db()
    assert orden.pagado is False
    assert not Pago.objects.filter(orden=orden).exists(), "un cobro fallido no deja rastro"


def test_el_pago_manual_rechaza_montos_no_positivos():
    class OrdenFalsa:
        pk = 1

    with pytest.raises(PagoRechazadoError):
        PagoManual().cobrar(OrdenFalsa(), Decimal("0"))

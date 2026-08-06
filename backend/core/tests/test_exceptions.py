"""Tests de las excepciones de dominio y su traducción a HTTP."""

from decimal import Decimal

import pytest
from rest_framework import status

from core.exceptions import (
    CantidadInvalidaError,
    CarritoVacioError,
    DescuentoInvalidoError,
    PagoRechazadoError,
    StockInsuficienteError,
    TienditaError,
)


def test_toda_excepcion_de_negocio_hereda_de_la_raiz():
    """Capturar TienditaError debe bastar para atrapar cualquier error de negocio."""
    for excepcion in (
        CarritoVacioError(),
        CantidadInvalidaError(0),
        StockInsuficienteError("Muñeca", 3, 2),
        DescuentoInvalidoError("VERANO", "está vencido"),
        PagoRechazadoError("fondos insuficientes"),
    ):
        assert isinstance(excepcion, TienditaError)


def test_stock_insuficiente_es_conflicto_no_peticion_invalida():
    """409, no 400: la petición está bien; lo que cambió es el inventario."""
    exc = StockInsuficienteError("Muñeca", solicitado=3, disponible=2)

    assert exc.http_status == status.HTTP_409_CONFLICT
    assert exc.codigo == "stock_insuficiente"


def test_stock_insuficiente_dice_cuanto_queda():
    """El frontend necesita el número para poder ofrecer 'llevar 2 en vez de 3'."""
    exc = StockInsuficienteError("Muñeca", solicitado=3, disponible=2)

    assert exc.detalle() == {"producto": "Muñeca", "solicitado": 3, "disponible": 2}
    assert "pediste 3 y quedan 2" in exc.mensaje


def test_carrito_vacio_es_peticion_invalida():
    exc = CarritoVacioError()

    assert exc.http_status == status.HTTP_400_BAD_REQUEST
    assert exc.codigo == "carrito_vacio"


def test_pago_rechazado_usa_402():
    exc = PagoRechazadoError("fondos insuficientes", monto=Decimal("9990"))

    assert exc.http_status == status.HTTP_402_PAYMENT_REQUIRED


def test_el_codigo_es_estable_y_no_depende_del_texto():
    """El frontend reacciona al código; el mensaje en español puede cambiar."""
    assert DescuentoInvalidoError("VERANO", "está vencido").codigo == "descuento_invalido"


def test_se_puede_capturar_por_tipo_concreto():
    with pytest.raises(StockInsuficienteError) as info:
        raise StockInsuficienteError("Pelota", 5, 1)

    assert info.value.disponible == 1

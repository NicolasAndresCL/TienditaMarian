"""Tests del despachador de eventos. Lógica pura: ni base de datos ni HTTP."""

import pytest

from core.events import Despachador, Evento


def test_el_suscriptor_recibe_el_evento():
    despachador = Despachador()
    recibidos = []
    despachador.suscribir(Evento.ORDEN_CREADA, recibidos.append)

    despachador.emitir(Evento.ORDEN_CREADA, "orden-1")

    assert recibidos == ["orden-1"]


def test_todos_los_suscriptores_reciben_el_evento():
    despachador = Despachador()
    recibidos_a, recibidos_b = [], []
    despachador.suscribir(Evento.ORDEN_CREADA, recibidos_a.append)
    despachador.suscribir(Evento.ORDEN_CREADA, recibidos_b.append)

    despachador.emitir(Evento.ORDEN_CREADA, "orden-1")

    assert recibidos_a == recibidos_b == ["orden-1"]


def test_suscribir_dos_veces_no_duplica_el_efecto():
    despachador = Despachador()
    recibidos = []
    despachador.suscribir(Evento.ORDEN_CREADA, recibidos.append)
    despachador.suscribir(Evento.ORDEN_CREADA, recibidos.append)

    despachador.emitir(Evento.ORDEN_CREADA, "orden-1")

    assert recibidos == ["orden-1"]


def test_un_suscriptor_que_falla_no_impide_a_los_demas():
    """Si el correo está caído, la notificación interna igual debe crearse."""
    despachador = Despachador()
    recibidos = []

    def explota(_orden):
        raise RuntimeError("servidor de correo caído")

    despachador.suscribir(Evento.ORDEN_CREADA, explota)
    despachador.suscribir(Evento.ORDEN_CREADA, recibidos.append)

    fallos = despachador.emitir(Evento.ORDEN_CREADA, "orden-1")

    assert recibidos == ["orden-1"], "el segundo suscriptor debe recibir el evento igual"
    assert len(fallos) == 1
    assert isinstance(fallos[0], RuntimeError)


def test_emitir_nunca_lanza():
    """La venta ya ocurrió: un efecto secundario roto no puede tumbarla."""
    despachador = Despachador()

    def explota(_orden):
        raise RuntimeError("todo mal")

    despachador.suscribir(Evento.ORDEN_CREADA, explota)

    despachador.emitir(Evento.ORDEN_CREADA, "orden-1")  # no debe lanzar


def test_emitir_sin_suscriptores_no_hace_nada():
    assert Despachador().emitir(Evento.ORDEN_PAGADA, "orden-1") == []


def test_desuscribir_corta_la_entrega():
    despachador = Despachador()
    recibidos = []
    despachador.suscribir(Evento.ORDEN_CREADA, recibidos.append)
    despachador.desuscribir(Evento.ORDEN_CREADA, recibidos.append)

    despachador.emitir(Evento.ORDEN_CREADA, "orden-1")

    assert recibidos == []


def test_los_eventos_no_se_cruzan():
    despachador = Despachador()
    creadas, pagadas = [], []
    despachador.suscribir(Evento.ORDEN_CREADA, creadas.append)
    despachador.suscribir(Evento.ORDEN_PAGADA, pagadas.append)

    despachador.emitir(Evento.ORDEN_CREADA, "orden-1")

    assert creadas == ["orden-1"]
    assert pagadas == []


@pytest.mark.parametrize(
    ("evento", "valor"),
    [(Evento.ORDEN_CREADA, "orden_creada"), (Evento.ORDEN_PAGADA, "orden_pagada")],
)
def test_los_eventos_tienen_un_valor_estable(evento, valor):
    assert evento.value == valor

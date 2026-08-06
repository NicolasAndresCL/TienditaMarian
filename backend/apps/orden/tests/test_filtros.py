"""Tests de los filtros del historial de órdenes.

Los dos bugs que cubren:

1. `if pagado is not None` daba verdadero también con `?pagado=` (cadena vacía),
   así que el historial se filtraba por `pagado=False` sin que nadie lo pidiera y
   las compras ya pagadas desaparecían de la lista.
2. `creado__lte='2026-07-14'` sobre un DateTimeField compara contra las 00:00 de
   ese día: **todas** las compras del último día quedaban fuera del rango.
"""

from datetime import date, timedelta

import pytest
from django.utils import timezone

from apps.orden.models import Orden
from apps.orden.selectors import filtrar_ordenes


@pytest.fixture
def ordenes(db, usuario):
    pagada = Orden.objects.create(usuario=usuario, total=1000, pagado=True)
    pendiente = Orden.objects.create(usuario=usuario, total=2000, pagado=False)
    return pagada, pendiente


@pytest.mark.django_db
def test_sin_filtro_de_pago_se_ven_todas(usuario, ordenes):
    assert filtrar_ordenes(usuario).count() == 2


@pytest.mark.django_db
def test_el_parametro_pagado_vacio_no_filtra_nada(usuario, ordenes):
    """Regresión: `?pagado=` escondía las órdenes pagadas."""
    assert filtrar_ordenes(usuario, pagado="").count() == 2
    assert filtrar_ordenes(usuario, pagado="   ").count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize("valor", ["true", "TRUE", "1", "si"])
def test_filtrar_por_pagadas(usuario, ordenes, valor):
    resultado = filtrar_ordenes(usuario, pagado=valor)

    assert resultado.count() == 1
    assert resultado.first().pagado is True


@pytest.mark.django_db
def test_filtrar_por_no_pagadas(usuario, ordenes):
    resultado = filtrar_ordenes(usuario, pagado="false")

    assert resultado.count() == 1
    assert resultado.first().pagado is False


@pytest.mark.django_db
def test_la_orden_de_hoy_entra_en_el_rango_que_termina_hoy(usuario, ordenes):
    """Regresión: la comparación contra las 00:00 dejaba fuera todo el último día."""
    hoy = date.today().isoformat()

    resultado = filtrar_ordenes(usuario, fecha_inicio=hoy, fecha_fin=hoy)

    assert resultado.count() == 2, "las compras de hoy deben entrar en el rango de hoy"


@pytest.mark.django_db
def test_una_orden_antigua_queda_fuera_del_rango(usuario, ordenes):
    vieja = Orden.objects.create(usuario=usuario, total=500)
    Orden.objects.filter(pk=vieja.pk).update(creado=timezone.now() - timedelta(days=10))

    hoy = date.today().isoformat()
    resultado = filtrar_ordenes(usuario, fecha_inicio=hoy, fecha_fin=hoy)

    assert vieja not in resultado


@pytest.mark.django_db
def test_una_fecha_con_formato_invalido_se_ignora_sin_romper(usuario, ordenes):
    """Un filtro mal escrito no puede tumbar el historial de compras."""
    assert filtrar_ordenes(usuario, fecha_inicio="ayer", fecha_fin="14/07/2026").count() == 2


@pytest.mark.django_db
def test_el_historial_no_muestra_las_ordenes_de_otro(usuario, otro_usuario, ordenes):
    Orden.objects.create(usuario=otro_usuario, total=9999)

    assert filtrar_ordenes(usuario).count() == 2

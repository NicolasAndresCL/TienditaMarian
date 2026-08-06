"""Consultas de lectura sobre órdenes.

Capa de acceso a datos (skill §2.1): aquí viven los querysets, con sus
`select_related` / `prefetch_related`. Las vistas piden datos; no arman consultas.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet

from apps.orden.models import Orden

logger = logging.getLogger(__name__)


def _parsear_fecha(valor: str | None) -> date | None:
    """Convierte 'YYYY-MM-DD' en date. Devuelve None si no se puede.

    No lanza: un filtro mal escrito en la query string no debe tumbar el
    historial de compras, solo ignorarse (skill §2.2).
    """
    if not valor:
        return None

    try:
        return datetime.strptime(valor.strip(), "%Y-%m-%d").date()
    except ValueError:
        logger.info("Fecha ignorada por formato inválido: %r", valor)
        return None


def _parsear_booleano(valor: str | None) -> bool | None:
    """Interpreta el parámetro `pagado`. Devuelve None si no hay filtro.

    El código anterior hacía `if pagado is not None`, que es cierto incluso con
    `?pagado=` (cadena vacía): el historial se filtraba por `pagado=False` sin
    que nadie lo hubiera pedido, y las compras pagadas desaparecían de la lista.
    """
    if valor is None or not valor.strip():
        return None

    return valor.strip().lower() in {"true", "1", "si", "sí"}


def ordenes_de(usuario: AbstractBaseUser) -> QuerySet[Orden]:
    """Órdenes del usuario, listas para serializar sin N+1."""
    return (
        Orden.objects.filter(usuario=usuario)
        .select_related("usuario")
        .prefetch_related("items__producto")
    )


def filtrar_ordenes(
    usuario: AbstractBaseUser,
    *,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    pagado: str | None = None,
) -> QuerySet[Orden]:
    queryset = ordenes_de(usuario)

    if (desde := _parsear_fecha(fecha_inicio)) is not None:
        queryset = queryset.filter(creado__date__gte=desde)

    if (hasta := _parsear_fecha(fecha_fin)) is not None:
        # `creado` es un DateTimeField. El código anterior comparaba
        # `creado__lte='2026-07-14'`, que Django interpreta como las 00:00 de ese
        # día: TODAS las compras del último día quedaban fuera del filtro.
        # `__date__lte` compara solo la fecha e incluye el día completo.
        queryset = queryset.filter(creado__date__lte=hasta)

    if (esta_pagado := _parsear_booleano(pagado)) is not None:
        queryset = queryset.filter(pagado=esta_pagado)

    return queryset


def ordenes_del_ultimo_mes(usuario: AbstractBaseUser) -> QuerySet[Orden]:
    return ordenes_de(usuario).filter(creado__gte=date.today() - timedelta(days=30))

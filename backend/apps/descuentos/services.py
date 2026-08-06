"""Reglas de negocio de los descuentos.

Hasta ahora la app `descuentos` existía pero **nadie la usaba**: el checkout
cobraba el precio de lista y jamás miraba un cupón. Aquí queda la lógica que
faltaba para conectarla.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from apps.descuentos.models import Descuento
from core.exceptions import DescuentoInvalidoError

logger = logging.getLogger(__name__)

CERO = Decimal("0.00")
CIEN = Decimal("100")


class DescuentoService:
    """Valida y aplica cupones sobre un subtotal.

    `calcular_total` es una función pura: recibe un subtotal y un `Descuento` y
    devuelve el total. No toca la base ni la red, así que se puede probar entera
    con `pytest.raises` y aritmética.
    """

    @staticmethod
    def buscar(cupon: str) -> Descuento:
        """Busca un cupón vigente por nombre. Lanza si no sirve."""
        descuento = Descuento.objects.filter(nombre__iexact=cupon.strip()).first()

        if descuento is None:
            raise DescuentoInvalidoError(cupon, "no existe")

        DescuentoService.validar(descuento)
        return descuento

    @staticmethod
    def validar(descuento: Descuento, hoy: date | None = None) -> None:
        """Comprueba que el cupón esté activo y dentro de su ventana de fechas.

        `hoy` es un parámetro y no `date.today()` incrustado: así el test puede
        situarse en cualquier fecha sin congelar el reloj del sistema.
        """
        hoy = hoy or date.today()

        if not descuento.activo:
            raise DescuentoInvalidoError(descuento.nombre, "está desactivado")

        if hoy < descuento.fecha_inicio:
            raise DescuentoInvalidoError(descuento.nombre, "todavía no empieza")

        if hoy > descuento.fecha_fin:
            raise DescuentoInvalidoError(descuento.nombre, "está vencido")

    @staticmethod
    def calcular_total(subtotal: Decimal, descuento: Descuento | None) -> Decimal:
        """Aplica el descuento al subtotal. Nunca devuelve un total negativo."""
        if descuento is None:
            return subtotal

        if descuento.tipo == "porcentaje":
            rebaja = subtotal * (descuento.valor / CIEN)
        else:  # monto fijo
            rebaja = descuento.valor

        # Un cupón de $5.000 sobre una compra de $3.000 no puede dejar un total
        # de -$2.000: la tienda no le paga al cliente por comprar.
        total = max(subtotal - rebaja, CERO)

        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def aplicar(subtotal: Decimal, cupon: str | None) -> tuple[Decimal, Descuento | None]:
        """Punto de entrada del checkout: del cupón en texto al total final."""
        if not cupon:
            return subtotal, None

        descuento = DescuentoService.buscar(cupon)
        total = DescuentoService.calcular_total(subtotal, descuento)

        logger.info(
            "Cupón aplicado: %s (%s %s) subtotal=%s total=%s",
            descuento.nombre,
            descuento.tipo,
            descuento.valor,
            subtotal,
            total,
        )
        return total, descuento

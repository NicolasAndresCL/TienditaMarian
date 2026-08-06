"""Cobro de órdenes.

`PasarelaPago` es la frontera del dominio con el mundo exterior. Hoy solo existe
`PagoManual` (la transferencia que Marian confirma a mano), pero cuando entre
Webpay o Stripe bastará con una subclase: ni el checkout ni las órdenes se
enteran, porque hablan con la interfaz y no con la implementación.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from decimal import Decimal

from django.db import transaction

from apps.orden.models import Orden
from apps.pagos.models import Pago
from core.events import Evento
from core.events import despachador as despachador_global
from core.exceptions import OrdenYaPagadaError, PagoRechazadoError

logger = logging.getLogger(__name__)


class PasarelaPago(ABC):
    """Contrato que cumple cualquier medio de pago."""

    nombre: str

    @abstractmethod
    def cobrar(self, orden: Orden, monto: Decimal) -> str:
        """Cobra y devuelve el identificador de la transacción.

        Lanza `PagoRechazadoError` si el cobro no prospera.
        """


class PagoManual(PasarelaPago):
    """Transferencia bancaria que la tienda confirma a mano."""

    nombre = "manual"

    def cobrar(self, orden: Orden, monto: Decimal) -> str:
        if monto <= 0:
            raise PagoRechazadoError("el monto debe ser mayor que cero", monto)
        return f"MANUAL-{orden.pk}"


class PagoService:
    """Registra el cobro de una orden y la marca como pagada."""

    def __init__(self, pasarela: PasarelaPago | None = None, despachador=None) -> None:
        self.pasarela = pasarela or PagoManual()
        self.despachador = despachador or despachador_global

    @transaction.atomic
    def cobrar(self, orden: Orden) -> Pago:
        # Se bloquea la fila para que dos confirmaciones simultáneas del mismo
        # pago no marquen la orden dos veces.
        orden = Orden.objects.select_for_update().get(pk=orden.pk)

        if orden.pagado:
            raise OrdenYaPagadaError()

        transaccion_id = self.pasarela.cobrar(orden, orden.total)

        pago = Pago.objects.create(
            usuario=orden.usuario,
            orden=orden,
            monto=orden.total,
            metodo=self.pasarela.nombre,
            estado="pagado",
            transaccion_id=transaccion_id,
        )

        orden.pagado = True
        orden.save(update_fields=["pagado"])

        transaction.on_commit(lambda: self.despachador.emitir(Evento.ORDEN_PAGADA, orden))
        logger.info(
            "Orden %s pagada: monto=%s metodo=%s transaccion=%s",
            orden.pk,
            orden.total,
            self.pasarela.nombre,
            transaccion_id,
        )
        return pago

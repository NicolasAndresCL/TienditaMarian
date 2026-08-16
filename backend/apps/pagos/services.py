"""Cobro de órdenes.

`PasarelaPago` es la frontera del dominio con el mundo exterior: `PagoManual` es
la transferencia que Marian confirma a mano, y ni el checkout ni las órdenes
saben cuál se está usando porque hablan con la interfaz.

Webpay no cabe en esa interfaz, y no por capricho: `cobrar()` supone que el
dinero se mueve dentro de una llamada, mientras que Webpay **manda a la clienta
a otro sitio** y vuelve después por una petición distinta. Son dos formas
distintas de cobrar, así que hay dos abstracciones:

    PasarelaPago        cobrar(orden, monto) -> id de transacción     [síncrona]
    PasarelaRedirigida  iniciar(...) -> a dónde ir · confirmar(token) [en dos pasos]
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
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


# --------------------------------------------------------------- Webpay Plus


@dataclass(frozen=True)
class IntencionDePago:
    """A dónde hay que mandar a la clienta para que pague, y con qué token."""

    url: str
    token: str


class PasarelaRedirigida(ABC):
    """Pasarela que cobra en dos pasos, con una visita a otro sitio en medio."""

    nombre: str

    @abstractmethod
    def iniciar(self, buy_order: str, session_id: str, monto: int, url_retorno: str) -> IntencionDePago:
        """Reserva la transacción y devuelve a dónde enviar a la clienta."""

    @abstractmethod
    def confirmar(self, token: str) -> dict:
        """Cierra la transacción y devuelve la respuesta cruda de la pasarela."""


class PagoWebpay(PasarelaRedirigida):
    """Webpay Plus de Transbank.

    La transacción del SDK se inyecta para poder probar el servicio sin salir a
    la red; por defecto se construye con las credenciales del entorno.
    """

    nombre = "webpay"

    def __init__(self, transaccion=None) -> None:
        self._transaccion = transaccion

    @property
    def transaccion(self):
        if self._transaccion is None:
            # El import va aquí y no arriba para que el módulo se pueda importar
            # (y el resto de pagos funcionar) aunque el SDK no esté instalado.
            from transbank.webpay.webpay_plus.transaction import Transaction

            constructor = (
                Transaction.build_for_production
                if settings.WEBPAY_PRODUCCION
                else Transaction.build_for_integration
            )
            self._transaccion = constructor(
                settings.WEBPAY_COMMERCE_CODE, settings.WEBPAY_API_KEY
            )
        return self._transaccion

    def iniciar(self, buy_order: str, session_id: str, monto: int, url_retorno: str) -> IntencionDePago:
        respuesta = self.transaccion.create(
            buy_order=buy_order, session_id=session_id, amount=monto, return_url=url_retorno
        )
        return IntencionDePago(url=respuesta["url"], token=respuesta["token"])

    def confirmar(self, token: str) -> dict:
        return self.transaccion.commit(token)


class WebpayService:
    """Orquesta el cobro con redirección.

    El flujo tiene dos entradas separadas en el tiempo y en la sesión:

        iniciar(orden)   ← la clienta, autenticada, pide pagar
        ...se va a Transbank, paga, y vuelve...
        confirmar(token) ← llega un POST cross-site SIN sesión

    Por eso `confirmar` no recibe usuario: se identifica por el token, que es un
    secreto de un solo uso emitido por Transbank y guardado en el `Pago`.
    """

    def __init__(self, pasarela: PasarelaRedirigida | None = None, despachador=None) -> None:
        self.pasarela = pasarela or PagoWebpay()
        self.despachador = despachador or despachador_global

    @transaction.atomic
    def iniciar(self, orden: Orden) -> IntencionDePago:
        orden = Orden.objects.select_for_update().get(pk=orden.pk)

        if orden.pagado:
            raise OrdenYaPagadaError()

        # `buy_order` identifica el INTENTO, no la orden: si un primer pago se
        # rechaza y la clienta reintenta, Transbank rechazaría un buy_order
        # repetido. Va acotado a 26 caracteres, que es el máximo que admite.
        buy_order = f"{orden.pk}-{uuid.uuid4().hex[:8]}"

        intencion = self.pasarela.iniciar(
            buy_order=buy_order,
            session_id=f"orden-{orden.pk}",
            # Webpay trabaja en pesos enteros: el peso chileno no tiene decimales.
            monto=int(orden.total),
            url_retorno=settings.WEBPAY_URL_RETORNO,
        )

        # El pago queda `pendiente` con el token guardado: es lo que permite
        # reconocer la vuelta, que llega sin sesión.
        Pago.objects.create(
            usuario=orden.usuario,
            orden=orden,
            monto=orden.total,
            metodo=self.pasarela.nombre,
            estado="pendiente",
            transaccion_id=intencion.token,
        )

        logger.info("Webpay iniciado: orden=%s buy_order=%s", orden.pk, buy_order)
        return intencion

    def confirmar(self, token: str) -> Pago:
        """Cierra el cobro. Idempotente: reconfirmar no vuelve a cobrar.

        La llamada a Transbank se hace **fuera** de la transacción, por dos
        motivos que se descubrieron a base de tests:

        - envolverlo todo en un `atomic` hacía que, al lanzar
          `PagoRechazadoError`, el rollback se llevara por delante el propio
          marcado de "fallido": el pago se quedaba «pendiente» para siempre;
        - y mantenía las filas bloqueadas durante toda la latencia de la
          pasarela, que es red y puede tardar lo que quiera.
        """
        pago = Pago.objects.select_related("orden").get(
            transaccion_id=token, metodo=self.pasarela.nombre
        )

        # La clienta puede recargar la página de retorno, o Transbank reintentar:
        # si ya se cerró, se devuelve el resultado que hubo.
        if pago.estado != "pendiente":
            return pago

        respuesta = self.pasarela.confirmar(token)

        # Transbank considera exitosa la transacción SOLO si se cumplen LAS DOS
        # condiciones. Comprobar una sola daría por pagada una que no lo está.
        autorizada = (
            str(respuesta.get("response_code")) == "0"
            and respuesta.get("status") == "AUTHORIZED"
        )

        with transaction.atomic():
            # Se relee bajo bloqueo: entre la lectura de arriba y este punto pudo
            # entrar otra confirmación del mismo token (un doble retorno).
            pago = Pago.objects.select_for_update().select_related("orden").get(pk=pago.pk)
            if pago.estado != "pendiente":
                return pago

            pago.estado = "pagado" if autorizada else "fallido"
            pago.save(update_fields=["estado"])

            if autorizada:
                orden = pago.orden
                orden.pagado = True
                orden.save(update_fields=["pagado"])
                transaction.on_commit(
                    lambda: self.despachador.emitir(Evento.ORDEN_PAGADA, orden)
                )

        if not autorizada:
            logger.warning(
                "Webpay rechazó la orden %s: status=%s response_code=%s",
                pago.orden_id,
                respuesta.get("status"),
                respuesta.get("response_code"),
            )
            raise PagoRechazadoError("la transacción no fue autorizada", pago.monto)

        logger.info("Webpay confirmó la orden %s por %s", pago.orden_id, pago.monto)
        return pago

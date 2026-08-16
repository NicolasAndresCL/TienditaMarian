"""Vistas de pagos.

Antes: `Pago.objects.all()` con `IsAuthenticated` y un serializer con
`fields = '__all__'`. Eso permitía dos abusos distintos:

1. leer los pagos de todo el mundo (montos e identificadores de transacción);
2. crear un pago con `{"usuario": <ajeno>, "estado": "pagado"}` y dar por saldada
   la orden de otra persona.

Ahora el dueño se fija desde `request.user` y el `estado` lo decide la pasarela,
nunca el cliente.
"""

import logging

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.orden.selectors import ordenes_de
from apps.orden.serializers import OrdenSerializer
from apps.pagos.models import Pago
from apps.pagos.serializers import PagoSerializer
from apps.pagos.services import PagoService, WebpayService
from core.api.base_views import BaseListCreateView, PorDuenoMixin
from core.exceptions import TienditaError

logger = logging.getLogger(__name__)


@extend_schema_view(
    get=extend_schema(
        summary="Listar mis pagos",
        description="Devuelve los pagos del usuario autenticado. El staff los ve todos.",
        tags=["Pagos"],
        operation_id="listarPagos",
    ),
    post=extend_schema(
        summary="Registrar un pago",
        description="Registra un pago sobre una orden propia. Nace en estado «pendiente».",
        tags=["Pagos"],
        operation_id="crearPago",
    ),
)
class PagoListCreateView(PorDuenoMixin, BaseListCreateView):
    queryset = Pago.objects.select_related("orden", "usuario")
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    post=extend_schema(
        summary="Pagar una orden",
        description=(
            "Cobra la orden con la pasarela configurada, la marca como pagada y "
            "emite el evento `ORDEN_PAGADA` (correo y notificación). La operación "
            "es idempotente: reintentarla sobre una orden ya pagada devuelve 409, "
            "nunca un segundo cobro."
        ),
        tags=["Pagos"],
        operation_id="pagarOrden",
        request=None,
        responses={
            200: OrdenSerializer,
            402: OpenApiResponse(description="La pasarela rechazó el pago."),
            404: OpenApiResponse(description="La orden no existe o no es tuya."),
            409: OpenApiResponse(description="La orden ya estaba pagada."),
        },
    )
)
class PagarOrdenView(GenericAPIView):
    """Cobra una orden propia.

    Este endpoint **no existía**. `PagoService` —con su bloqueo de fila, su
    idempotencia y la emisión de `ORDEN_PAGADA`— estaba escrito y probado, y no
    lo llamaba nadie salvo los tests: `POST /pagos/` solo creaba una fila en
    estado `pendiente`, sin cobrar nada ni tocar la orden. Por eso las órdenes se
    quedaban en "Pendiente" para siempre.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = OrdenSerializer

    def get_queryset(self):
        # `ordenes_de` ya filtra por dueño: pagar la orden de otra persona ni
        # siquiera es un 403, es un 404 — esa orden no existe para quien pregunta.
        return ordenes_de(self.request.user)

    def post(self, request: Request, pk: int) -> Response:
        orden = self.get_object()
        PagoService().cobrar(orden)

        orden.refresh_from_db()
        return Response(self.get_serializer(orden).data, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        summary="Iniciar el pago con Webpay",
        description=(
            "Reserva la transacción en Transbank y devuelve la URL a la que hay "
            "que redirigir a la clienta, junto con el `token_ws` que debe viajar "
            "como campo de formulario."
        ),
        tags=["Pagos"],
        operation_id="iniciarPagoWebpay",
        request=None,
        responses={
            200: OpenApiResponse(description="Transacción creada: url + token."),
            404: OpenApiResponse(description="La orden no existe o no es tuya."),
            409: OpenApiResponse(description="La orden ya estaba pagada."),
        },
    )
)
class IniciarWebpayView(GenericAPIView):
    """Primer paso del pago con redirección."""

    permission_classes = [IsAuthenticated]
    serializer_class = None

    def get_queryset(self):
        return ordenes_de(self.request.user)

    def post(self, request: Request, pk: int) -> Response:
        intencion = WebpayService().iniciar(self.get_object())
        return Response({"url": intencion.url, "token": intencion.token})


@extend_schema_view(
    post=extend_schema(
        summary="Retorno de Webpay (uso interno de Transbank)",
        description=(
            "Transbank devuelve aquí el control cuando la clienta termina. "
            "Confirma la transacción y redirige al frontend con el resultado."
        ),
        tags=["Pagos"],
        operation_id="retornoWebpay",
        request=None,
        responses={302: OpenApiResponse(description="Redirección al frontend.")},
    )
)
@method_decorator(csrf_exempt, name="dispatch")
class RetornoWebpayView(GenericAPIView):
    """Segundo paso: la vuelta desde Transbank.

    Es **público a propósito**, y esa decisión no es negociable con el diseño de
    la sesión: Transbank devuelve el control con un POST desde SU dominio, y una
    cookie `SameSite=Lax` no viaja en un POST cross-site. Si este endpoint
    exigiera sesión, ningún pago podría confirmarse jamás.

    Lo que lo autentica es el `token_ws`: un secreto de un solo uso que emitió
    Transbank y que solo está en dos sitios, su servidor y nuestra fila de
    `Pago`. Quien no lo tenga no puede confirmar nada, y quien lo tenga solo
    puede cerrar la transacción a la que pertenece.

    Acepta GET además de POST porque Transbank usa uno u otro según la versión
    de la API y según cómo termine el flujo (pago anulado por la clienta).
    """

    permission_classes = [AllowAny]
    # Sin autenticación en absoluto: si la clase de auth por cookie corriera
    # aquí, exigiría CSRF a una petición que por definición viene de otro sitio.
    authentication_classes = []
    serializer_class = None

    def post(self, request: Request) -> HttpResponseRedirect:
        return self._resolver(request.data or request.query_params)

    def get(self, request: Request) -> HttpResponseRedirect:
        return self._resolver(request.query_params)

    def _resolver(self, datos) -> HttpResponseRedirect:
        token = datos.get("token_ws")

        # Sin `token_ws` la clienta anuló el pago en el formulario de Transbank,
        # que en ese caso devuelve `TBK_TOKEN`. No es un error: es un "no quiso".
        if not token:
            logger.info("Retorno de Webpay sin token_ws: pago anulado por la clienta")
            return self._al_frontend(estado="anulado")

        try:
            pago = WebpayService().confirmar(token)
        except Pago.DoesNotExist:
            logger.warning("Retorno de Webpay con un token desconocido")
            return self._al_frontend(estado="desconocido")
        except TienditaError as exc:
            logger.info("Retorno de Webpay rechazado: %s", exc.codigo)
            return self._al_frontend(estado="rechazado")

        return self._al_frontend(estado="pagado", orden=pago.orden_id)

    def _al_frontend(self, estado: str, orden: int | None = None) -> HttpResponseRedirect:
        """Devuelve a la clienta a la tienda con el resultado en la URL."""
        destino = f"{settings.WEBPAY_URL_FRONTEND}/compra"
        if orden is not None:
            destino = f"{destino}/{orden}"
        return HttpResponseRedirect(f"{destino}?pago={estado}")

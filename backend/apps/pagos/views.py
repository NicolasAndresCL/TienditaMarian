"""Vistas de pagos.

Antes: `Pago.objects.all()` con `IsAuthenticated` y un serializer con
`fields = '__all__'`. Eso permitía dos abusos distintos:

1. leer los pagos de todo el mundo (montos e identificadores de transacción);
2. crear un pago con `{"usuario": <ajeno>, "estado": "pagado"}` y dar por saldada
   la orden de otra persona.

Ahora el dueño se fija desde `request.user` y el `estado` lo decide la pasarela,
nunca el cliente.
"""

from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.orden.selectors import ordenes_de
from apps.orden.serializers import OrdenSerializer
from apps.pagos.models import Pago
from apps.pagos.serializers import PagoSerializer
from apps.pagos.services import PagoService
from core.api.base_views import BaseListCreateView, PorDuenoMixin


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

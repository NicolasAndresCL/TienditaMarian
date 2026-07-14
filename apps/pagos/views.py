"""Vistas de pagos.

Antes: `Pago.objects.all()` con `IsAuthenticated` y un serializer con
`fields = '__all__'`. Eso permitía dos abusos distintos:

1. leer los pagos de todo el mundo (montos e identificadores de transacción);
2. crear un pago con `{"usuario": <ajeno>, "estado": "pagado"}` y dar por saldada
   la orden de otra persona.

Ahora el dueño se fija desde `request.user` y el `estado` lo decide la pasarela,
nunca el cliente.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import IsAuthenticated

from apps.pagos.models import Pago
from apps.pagos.serializers import PagoSerializer
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

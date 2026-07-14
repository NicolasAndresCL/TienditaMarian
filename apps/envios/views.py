"""Vistas de envíos.

Antes: `queryset = Envio.objects.all()` con solo `IsAuthenticated`. Cualquier
cliente registrado podía listar, leer, editar y borrar los envíos de **todas** las
clientas, con su dirección, ciudad y código postal. Era la peor fuga del proyecto.

Ahora `PorDuenoMixin` filtra el queryset por dueño (el listado deja de mostrar lo
ajeno) y `EsDuenoOAdmin` corta el acceso directo por id.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import IsAuthenticated

from apps.envios.models import Envio
from apps.envios.serializers import EnvioSerializer
from core.api.base_views import BaseListCreateView, BaseRetrieveUpdateDestroyView, PorDuenoMixin
from core.api.permissions import EsDuenoOAdmin


@extend_schema_view(
    get=extend_schema(
        summary="Listar mis envíos",
        description="Devuelve los envíos del usuario autenticado. El staff los ve todos.",
        tags=["Envíos"],
        operation_id="listarEnvios",
    ),
    post=extend_schema(
        summary="Registrar nuevo envío",
        description="Crea un envío asociado a una orden propia.",
        tags=["Envíos"],
        operation_id="crearEnvio",
    ),
)
class EnvioListCreateView(PorDuenoMixin, BaseListCreateView):
    queryset = Envio.objects.select_related("orden", "usuario")
    serializer_class = EnvioSerializer
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    get=extend_schema(
        summary="Detalle de un envío propio", tags=["Envíos"], operation_id="detalleEnvio"
    ),
    put=extend_schema(summary="Actualizar envío", tags=["Envíos"], operation_id="actualizarEnvio"),
    patch=extend_schema(
        summary="Actualizar envío parcialmente",
        tags=["Envíos"],
        operation_id="actualizarEnvioParcial",
    ),
    delete=extend_schema(summary="Eliminar envío", tags=["Envíos"], operation_id="eliminarEnvio"),
)
class EnvioDetailView(PorDuenoMixin, BaseRetrieveUpdateDestroyView):
    queryset = Envio.objects.select_related("orden", "usuario")
    serializer_class = EnvioSerializer
    permission_classes = [IsAuthenticated, EsDuenoOAdmin]

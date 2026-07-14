"""Vistas de analítica.

El permiso estaba **invertido**: con `IsAuthenticatedOrReadOnly`, cualquier
visitante sin cuenta podía hacer GET y llevarse el historial completo de eventos
—qué miró cada usuario, qué buscó, qué compró— mientras que para *escribir* un
evento sí se pedía sesión.

Lo correcto es al revés: registrar un evento es una acción rutinaria del cliente
autenticado; leer la analítica del negocio es cosa de la dueña de la tienda.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from apps.analytics.models import AnalyticsEvent
from apps.analytics.serializers import AnalyticsEventSerializer
from core.api.base_views import BaseListCreateView


@extend_schema_view(
    get=extend_schema(
        summary="Listar eventos analíticos",
        description="Historial de eventos. Solo la administración de la tienda.",
        tags=["Analytics"],
        operation_id="listarEventosAnalytics",
    ),
    post=extend_schema(
        summary="Registrar evento analítico",
        description="Registra un evento a nombre del usuario autenticado.",
        tags=["Analytics"],
        operation_id="crearEventoAnalytics",
    ),
)
class AnalyticsEventListCreateView(BaseListCreateView):
    queryset = AnalyticsEvent.objects.select_related("usuario")
    serializer_class = AnalyticsEventSerializer

    def get_permissions(self):
        # Leer el comportamiento de toda la clientela es un privilegio de staff;
        # emitir un evento propio, no.
        if self.request.method == "GET":
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer) -> None:
        serializer.save(usuario=self.request.user)

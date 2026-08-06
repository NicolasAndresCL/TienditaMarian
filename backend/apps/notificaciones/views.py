"""Vistas de notificaciones.

Antes `Notificacion.objects.all()` con `IsAuthenticated`: cualquier cliente leía
las notificaciones de todos los demás (qué compraron, cuándo, por cuánto).
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from apps.notificaciones.models import Notificacion
from apps.notificaciones.serializers import NotificacionSerializer
from core.api.base_views import BaseListCreateView, BaseRetrieveUpdateDestroyView, PorDuenoMixin
from core.api.permissions import EsDuenoOAdmin


@extend_schema_view(
    get=extend_schema(
        summary="Listar mis notificaciones",
        description="Notificaciones del usuario autenticado. El staff las ve todas.",
        tags=["Notificaciones"],
        operation_id="listarNotificaciones",
    ),
    post=extend_schema(
        summary="Crear notificación",
        description="Solo la administración: las notificaciones normales las emite el sistema.",
        tags=["Notificaciones"],
        operation_id="crearNotificacion",
    ),
)
class NotificacionListCreateView(PorDuenoMixin, BaseListCreateView):
    queryset = Notificacion.objects.select_related("usuario")
    serializer_class = NotificacionSerializer

    def get_permissions(self):
        # Las notificaciones las genera el sistema al crearse una orden; un
        # cliente no tiene por qué fabricarse las suyas.
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [IsAuthenticated()]


@extend_schema_view(
    get=extend_schema(
        summary="Obtener notificación propia",
        tags=["Notificaciones"],
        operation_id="obtenerNotificacion",
    ),
    put=extend_schema(
        summary="Actualizar notificación",
        tags=["Notificaciones"],
        operation_id="actualizarNotificacion",
    ),
    patch=extend_schema(
        summary="Marcar notificación como leída",
        tags=["Notificaciones"],
        operation_id="actualizarNotificacionParcial",
    ),
    delete=extend_schema(
        summary="Eliminar notificación",
        tags=["Notificaciones"],
        operation_id="eliminarNotificacion",
    ),
)
class NotificacionDetailView(PorDuenoMixin, BaseRetrieveUpdateDestroyView):
    queryset = Notificacion.objects.select_related("usuario")
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated, EsDuenoOAdmin]

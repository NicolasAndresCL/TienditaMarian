from rest_framework import generics, mixins
from .models import Notificacion
from .serializers import NotificacionSerializer
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    get=extend_schema(
        summary="Listar notificaciones",
        description="Devuelve una lista de notificaciones registradas.\n\nReturns a list of registered notifications.",
        tags=["Notificaciones"],
        operation_id="listarNotificaciones"
    ),
    post=extend_schema(
        summary="Crear notificación",
        description="Registra una nueva notificación para un usuario.\n\nCreates a new notification for a user.",
        tags=["Notificaciones"],
        operation_id="crearNotificacion"
    )
)
class NotificacionListCreateView(mixins.ListModelMixin,
                                 mixins.CreateModelMixin,
                                 generics.GenericAPIView):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.list(request)

    def post(self, request, *args, **kwargs):
        return self.create(request)

@extend_schema_view(
    get=extend_schema(
        summary="Obtener notificación",
        description="Devuelve los detalles de una notificación específica.\n\nReturns details of a specific notification.",
        tags=["Notificaciones"],
        operation_id="obtenerNotificacion"
    ),
    put=extend_schema(
        summary="Actualizar notificación",
        description="Actualiza los datos de una notificación existente.\n\nUpdates an existing notification.",
        tags=["Notificaciones"],
        operation_id="actualizarNotificacion"
    ),
    delete=extend_schema(
        summary="Eliminar notificación",
        description="Elimina una notificación.\n\nDeletes a notification.",
        tags=["Notificaciones"],
        operation_id="eliminarNotificacion"
    )
)
class NotificacionDetailView(mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.DestroyModelMixin,
                             generics.GenericAPIView):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request)

    def put(self, request, *args, **kwargs):
        return self.update(request)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request)

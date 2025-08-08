from rest_framework import generics, mixins
from .models import Envio
from .serializers import EnvioSerializer
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    get=extend_schema(
        summary="Listar envíos",
        description="Devuelve una lista de envíos registrados.\n\nReturns a list of registered shipments.",
        tags=["Envíos"],
        operation_id="listarEnvios"
    ),
    post=extend_schema(
        summary="Registrar nuevo envío",
        description="Crea un nuevo registro de envío asociado a una orden.\n\nCreates a new shipment linked to an order.",
        tags=["Envíos"],
        operation_id="crearEnvio"
    )
)
class EnvioListCreateView(mixins.ListModelMixin,
                          mixins.CreateModelMixin,
                          generics.GenericAPIView):
    queryset = Envio.objects.all()
    serializer_class = EnvioSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.list(request)

    def post(self, request, *args, **kwargs):
        return self.create(request)

@extend_schema_view(
    get=extend_schema(
        summary="Obtener detalle de envío",
        description="Devuelve los datos de un envío específico.\n\nReturns details of a specific shipment.",
        tags=["Envíos"],
        operation_id="detalleEnvio"
    ),
    put=extend_schema(
        summary="Actualizar envío",
        description="Actualiza los datos de un envío existente.\n\nUpdates an existing shipment.",
        tags=["Envíos"],
        operation_id="actualizarEnvio"
    ),
    delete=extend_schema(
        summary="Eliminar envío",
        description="Elimina un envío por ID.\n\nDeletes a shipment by ID.",
        tags=["Envíos"],
        operation_id="eliminarEnvio"
    )
)
class EnvioDetailView(mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      generics.GenericAPIView):
    queryset = Envio.objects.all()
    serializer_class = EnvioSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request)

    def put(self, request, *args, **kwargs):
        return self.update(request)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request)

from rest_framework import generics, mixins
from .models import Descuento
from .serializers import DescuentoSerializer
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    get=extend_schema(
        summary="Listar descuentos",
        description="Devuelve una lista de descuentos activos o registrados.\n\nReturns a list of active or registered discounts.",
        tags=["Descuentos"],
        operation_id="listarDescuentos"
    ),
    post=extend_schema(
        summary="Crear descuento",
        description="Registra un nuevo descuento aplicable.\n\nCreates a new applicable discount.",
        tags=["Descuentos"],
        operation_id="crearDescuento"
    )
)
class DescuentoListCreateView(mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              generics.GenericAPIView):
    queryset = Descuento.objects.all()
    serializer_class = DescuentoSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.list(request)

    def post(self, request, *args, **kwargs):
        return self.create(request)

@extend_schema_view(
    get=extend_schema(
        summary="Obtener descuento",
        description="Devuelve los detalles de un descuento específico.\n\nReturns details of a specific discount.",
        tags=["Descuentos"],
        operation_id="obtenerDescuento"
    ),
    put=extend_schema(
        summary="Actualizar descuento",
        description="Actualiza los datos de un descuento existente.\n\nUpdates an existing discount.",
        tags=["Descuentos"],
        operation_id="actualizarDescuento"
    ),
    delete=extend_schema(
        summary="Eliminar descuento",
        description="Elimina un descuento.\n\nDeletes a discount.",
        tags=["Descuentos"],
        operation_id="eliminarDescuento"
    )
)
class DescuentoDetailView(mixins.RetrieveModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.DestroyModelMixin,
                          generics.GenericAPIView):
    queryset = Descuento.objects.all()
    serializer_class = DescuentoSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request)

    def put(self, request, *args, **kwargs):
        return self.update(request)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request)

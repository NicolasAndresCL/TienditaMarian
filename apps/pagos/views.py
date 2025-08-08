from rest_framework import generics, mixins
from .models import Pago
from .serializers import PagoSerializer
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    get=extend_schema(
        summary="Listar pagos",
        description="Devuelve una lista de todos los pagos registrados.\n\nReturns a list of all registered payments.",
        tags=["Pagos"],
        operation_id="listarPagos"
    ),
    post=extend_schema(
        summary="Crear nuevo pago",
        description="Registra un nuevo pago asociado a una orden.\n\nRegisters a new payment linked to an order.",
        tags=["Pagos"],
        operation_id="crearPago"
    )
)
class PagoListCreateView(mixins.ListModelMixin,
                         mixins.CreateModelMixin,
                         generics.GenericAPIView):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.list(request)

    def post(self, request, *args, **kwargs):
        return self.create(request)

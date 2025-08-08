from rest_framework import generics, mixins
from .models import AnalyticsEvent
from .serializers import AnalyticsEventSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    get=extend_schema(
        summary="Listar eventos analíticos",
        description="Devuelve todos los eventos registrados en el sistema.\n\nReturns all analytics events.",
        tags=["Analytics"],
        operation_id="listarEventosAnalytics"
    ),
    post=extend_schema(
        summary="Registrar evento analítico",
        description="Registra un nuevo evento analítico.\n\nRegisters a new analytics event.",
        tags=["Analytics"],
        operation_id="crearEventoAnalytics"
    )
)
class AnalyticsEventListCreateView(mixins.ListModelMixin,
                                   mixins.CreateModelMixin,
                                   generics.GenericAPIView):
    queryset = AnalyticsEvent.objects.all().order_by('-timestamp')
    serializer_class = AnalyticsEventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        return self.list(request)

    def post(self, request, *args, **kwargs):
        return self.create(request)

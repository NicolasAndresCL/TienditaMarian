from rest_framework import mixins, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.marian_loader.models import HitoCarga
from apps.marian_loader.api.serializers import (
    HitoCargaCreateSerializer,
    HitoCargaSerializer
)
from apps.marian_loader.services import carga_service


@extend_schema_view(
    post=extend_schema(
        tags=["Cargador de Marian"],
        operation_id="createHitoCarga",
        summary="Crear nuevo hito de carga",
        description="Recibe un archivo CSV y lanza el proceso de importación de productos.",
        request=HitoCargaCreateSerializer,
        responses={201: HitoCargaSerializer}
    ),
    get=extend_schema(
        tags=["Cargador de Marian"],
        operation_id="listHitosCarga",
        summary="Listar todos los hitos de carga",
        description="Devuelve una lista paginada de los hitos de carga registrados.",
        responses={200: HitoCargaSerializer(many=True)}
    ),
)
class HitoCargaListCreateView(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    generics.GenericAPIView
):
    queryset = HitoCarga.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = HitoCargaCreateSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def perform_create(self, serializer, request):
        archivo = serializer.validated_data['archivo']
        hito = HitoCarga.objects.create(
            usuario=request.user,
            archivo=archivo.name,
            status=HitoCarga.IN_PROGRESS
        )
        carga_service.ejecutar_import(hito, archivo)
        return hito

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hito = self.perform_create(serializer, request)
        output = HitoCargaSerializer(hito, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=["Cargador de Marian"],
        operation_id="retrieveHitoCarga",
        summary="Obtener detalle de un hito de carga",
        description="Recupera el estado y los detalles de una carga por su ID.",
        responses={200: HitoCargaSerializer}
    )
)
class HitoCargaDetailView(generics.RetrieveAPIView):
    queryset = HitoCarga.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = HitoCargaSerializer

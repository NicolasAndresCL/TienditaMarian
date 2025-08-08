from rest_framework import generics, mixins
from .models import Review
from .serializers import ReviewSerializer
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    get=extend_schema(
        summary="Listar reviews",
        description="Devuelve una lista de reseñas registradas.\n\nReturns a list of registered reviews.",
        tags=["Reviews"],
        operation_id="listarReviews"
    ),
    post=extend_schema(
        summary="Crear review",
        description="Registra una nueva reseña para un producto.\n\nCreates a new review for a product.",
        tags=["Reviews"],
        operation_id="crearReview"
    )
)
class ReviewListCreateView(mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           generics.GenericAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.list(request)

    def post(self, request, *args, **kwargs):
        return self.create(request)

@extend_schema_view(
    get=extend_schema(
        summary="Obtener review",
        description="Devuelve los detalles de una reseña específica.\n\nReturns details of a specific review.",
        tags=["Reviews"],
        operation_id="obtenerReview"
    ),
    put=extend_schema(
        summary="Actualizar review",
        description="Actualiza los datos de una reseña existente.\n\nUpdates an existing review.",
        tags=["Reviews"],
        operation_id="actualizarReview"
    ),
    delete=extend_schema(
        summary="Eliminar review",
        description="Elimina una reseña.\n\nDeletes a review.",
        tags=["Reviews"],
        operation_id="eliminarReview"
    )
)
class ReviewDetailView(mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.DestroyModelMixin,
                       generics.GenericAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request)

    def put(self, request, *args, **kwargs):
        return self.update(request)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request)

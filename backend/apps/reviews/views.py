"""Vistas de reseñas.

Las reseñas se leen en público (son parte de la vitrina), pero cada quien escribe
las suyas: `EsAutorOSoloLectura` impide editar o borrar las ajenas, y
`perform_create` fija el autor desde `request.user` en vez de leerlo del cuerpo,
que era lo que permitía suplantar a otra persona.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer
from core.api.base_views import BaseListCreateView, BaseRetrieveUpdateDestroyView
from core.api.permissions import EsAutorOSoloLectura


@extend_schema_view(
    get=extend_schema(
        summary="Listar reseñas",
        description="Reseñas de los productos. Lectura pública.",
        tags=["Reviews"],
        operation_id="listarReviews",
    ),
    post=extend_schema(
        summary="Publicar una reseña",
        description="La reseña se publica siempre a nombre del usuario autenticado.",
        tags=["Reviews"],
        operation_id="crearReview",
    ),
)
class ReviewListCreateView(BaseListCreateView):
    queryset = Review.objects.select_related("producto", "usuario")
    serializer_class = ReviewSerializer
    permission_classes = [EsAutorOSoloLectura]

    def perform_create(self, serializer) -> None:
        serializer.save(usuario=self.request.user)


@extend_schema_view(
    get=extend_schema(summary="Obtener reseña", tags=["Reviews"], operation_id="obtenerReview"),
    put=extend_schema(
        summary="Actualizar mi reseña", tags=["Reviews"], operation_id="actualizarReview"
    ),
    patch=extend_schema(
        summary="Actualizar mi reseña parcialmente",
        tags=["Reviews"],
        operation_id="actualizarReviewParcial",
    ),
    delete=extend_schema(
        summary="Eliminar mi reseña", tags=["Reviews"], operation_id="eliminarReview"
    ),
)
class ReviewDetailView(BaseRetrieveUpdateDestroyView):
    queryset = Review.objects.select_related("producto", "usuario")
    serializer_class = ReviewSerializer
    permission_classes = [EsAutorOSoloLectura]

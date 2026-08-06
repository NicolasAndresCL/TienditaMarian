from rest_framework import serializers

from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer de reseñas.

    `usuario` es de solo lectura y lo fija la vista desde `request.user`. Con
    `fields = '__all__'` el campo era escribible: bastaba mandar
    `{"usuario": <id ajeno>}` para publicar una reseña **a nombre de otra
    persona**.
    """

    usuario = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "producto", "usuario", "comentario", "calificacion", "fecha_creacion"]
        read_only_fields = ["id", "usuario", "fecha_creacion"]

    def validate_calificacion(self, valor: int) -> int:
        # El modelo usa PositiveSmallIntegerField, que aceptaría un 9999.
        if not 1 <= valor <= 5:
            raise serializers.ValidationError("La calificación va de 1 a 5 estrellas.")
        return valor

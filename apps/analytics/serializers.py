from rest_framework import serializers

from apps.analytics.models import AnalyticsEvent


class AnalyticsEventSerializer(serializers.ModelSerializer):
    """El evento se registra siempre a nombre del usuario autenticado."""

    usuario = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = AnalyticsEvent
        fields = ["id", "tipo_evento", "usuario", "metadata", "timestamp"]
        read_only_fields = ["id", "usuario", "timestamp"]

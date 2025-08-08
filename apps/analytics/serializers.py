from rest_framework import serializers
from .models import AnalyticsEvent

class AnalyticsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsEvent
        fields = '__all__'
        read_only_fields = ['timestamp']

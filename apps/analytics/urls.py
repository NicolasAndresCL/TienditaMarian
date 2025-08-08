from django.urls import path
from .views import AnalyticsEventListCreateView

urlpatterns = [
    path('', AnalyticsEventListCreateView.as_view(), name='analytics-list-create'),
]

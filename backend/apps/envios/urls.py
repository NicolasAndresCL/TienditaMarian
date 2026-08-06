from django.urls import path

from .views import EnvioDetailView, EnvioListCreateView

urlpatterns = [
    path('', EnvioListCreateView.as_view(), name='envios-list-create'),
    path('<int:pk>/', EnvioDetailView.as_view(), name='envios-detail'),
]

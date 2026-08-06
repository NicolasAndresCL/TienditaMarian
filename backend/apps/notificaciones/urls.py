from django.urls import path

from .views import NotificacionDetailView, NotificacionListCreateView

urlpatterns = [
    path('', NotificacionListCreateView.as_view(), name='notificaciones-list-create'),
    path('<int:pk>/', NotificacionDetailView.as_view(), name='notificaciones-detail'),
]

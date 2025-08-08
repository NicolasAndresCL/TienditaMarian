from django.urls import path
from apps.orden.views import OrdenListView, OrdenDetailView

urlpatterns = [
    path('ordenes/', OrdenListView.as_view(), name='ordenes-list'),
    path('ordenes/<int:pk>/', OrdenDetailView.as_view(), name='ordenes-detail'),
]

from django.urls import path
from .views import DescuentoListCreateView, DescuentoDetailView

urlpatterns = [
    path('', DescuentoListCreateView.as_view(), name='descuentos-list-create'),
    path('<int:pk>/', DescuentoDetailView.as_view(), name='descuentos-detail'),
]

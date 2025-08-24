from django.urls import path
from .views import HitoCargaListCreateView, HitoCargaDetailView

urlpatterns = [
    path('', HitoCargaListCreateView.as_view(), name='hito-list-create'),
    path('<int:pk>/', HitoCargaDetailView.as_view(), name='hito-detail'),
]

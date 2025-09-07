from django.urls import path

from apps.productos.views.producto_views import (
    ProductoListView,
    ProductoCreateView,
    ProductoDetailView,
    ProductoUpdateView,
    ProductoPartialUpdateView,
    ProductoDeleteView,
)

urlpatterns = [

    # 📦 Productos CRUD modular
    path('', ProductoListView.as_view(), name='producto-list'),
    path('create/', ProductoCreateView.as_view(), name='producto-create'),
    path('<int:pk>/', ProductoDetailView.as_view(), name='producto-detail'),
    path('<int:pk>/update/', ProductoUpdateView.as_view(), name='producto-update'),
    path('<int:pk>/partial-update/', ProductoPartialUpdateView.as_view(), name='producto-partial-update'),
    path('<int:pk>/delete/', ProductoDeleteView.as_view(), name='producto-delete'),
]

from django.urls import path
from productos.views.home_view import home

from productos.views.producto_views import (
    ProductoListView,
    ProductoCreateView,
    ProductoDetailView,
    ProductoUpdateView,
    ProductoPartialUpdateView,
    ProductoDeleteView,
)

urlpatterns = [
    # 🏠 Home simple
    path('', home, name='home'),

    # 📦 Productos CRUD modular
    path('productos/', ProductoListView.as_view(), name='producto-list'),
    path('productos/create/', ProductoCreateView.as_view(), name='producto-create'),
    path('productos/<int:pk>/', ProductoDetailView.as_view(), name='producto-detail'),
    path('productos/<int:pk>/update/', ProductoUpdateView.as_view(), name='producto-update'),
    path('productos/<int:pk>/partial-update/', ProductoPartialUpdateView.as_view(), name='producto-partial-update'),
    path('productos/<int:pk>/delete/', ProductoDeleteView.as_view(), name='producto-delete'),
]

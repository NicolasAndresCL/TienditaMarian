"""Rutas DEPRECADAS de productos (v0).

Se conservan para no romper el frontend actual mientras se migra a `/api/v1/`.
Repiten el nombre de la app dentro de su propio prefijo
(`/api/productos/productos/`) y servían la vitrina HTML desde dentro del espacio
de la API. Las rutas buenas están en `config/api_urls.py`.
"""

from django.urls import path

from apps.productos.views.producto_views import (
    ProductoCreateView,
    ProductoDeleteView,
    ProductoDetailView,
    ProductoListView,
    ProductoPartialUpdateView,
    ProductoUpdateView,
)

urlpatterns = [
    # La vitrina HTML ya no cuelga de aquí: vive en `/`, fuera de `/api/`.
    path('productos/', ProductoListView.as_view(), name='producto-list-legacy'),
    path('productos/create/', ProductoCreateView.as_view(), name='producto-create-legacy'),
    path('productos/<int:pk>/', ProductoDetailView.as_view(), name='producto-detail-legacy'),
    path('productos/<int:pk>/update/', ProductoUpdateView.as_view(), name='producto-update-legacy'),
    path(
        'productos/<int:pk>/partial-update/',
        ProductoPartialUpdateView.as_view(),
        name='producto-partial-update-legacy',
    ),
    path('productos/<int:pk>/delete/', ProductoDeleteView.as_view(), name='producto-delete-legacy'),
]

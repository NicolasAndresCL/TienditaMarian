"""Rutas de la API v1.

Las rutas anteriores repetían el nombre de la app dentro de su propio prefijo
(`/api/productos/productos/`, `/api/carrito/carrito/add/`), y la vitrina HTML
colgaba de `/api/productos/`, dentro del espacio de la API.

Aquí quedan limpias y versionadas. Las viejas siguen respondiendo mientras se
migra el frontend (strangler-fig, skill §3): nada se rompe de golpe.

    /api/v1/productos/            GET (público) · POST (staff)
    /api/v1/productos/<pk>/       GET (público) · PUT/PATCH/DELETE (staff)
    /api/v1/carrito/              GET
    /api/v1/carrito/items/        POST agregar · PATCH cantidad · DELETE quitar
    /api/v1/carrito/vaciar/       DELETE
    /api/v1/checkout/             POST
    /api/v1/ordenes/              GET
    /api/v1/ordenes/<pk>/         GET
    /api/v1/envios/               GET · POST
    /api/v1/pagos/                GET · POST
    /api/v1/reviews/              GET (público) · POST
    /api/v1/descuentos/           GET · POST (staff)
    /api/v1/analytics/            GET (staff) · POST
    /api/v1/notificaciones/       GET
    /api/v1/auth/{token,refresh,register,logout}/
"""

from django.urls import include, path

from apps.carrito.views import (
    AddItemCarritoView,
    CarritoDetailView,
    CheckoutView,
    ClearCarritoView,
    RemoveItemCarritoView,
    UpdateCantidadCarritoView,
)
from apps.envios.views import EnvioDetailView, EnvioListCreateView
from apps.orden.views import OrdenDetailView, OrdenListView
from apps.productos.views.producto_views import (
    ProductoCreateView,
    ProductoDeleteView,
    ProductoDetailView,
    ProductoListView,
    ProductoPartialUpdateView,
    ProductoUpdateView,
)

app_name = "v1"

productos_patterns = [
    path("", ProductoListView.as_view(), name="producto-list"),
    path("crear/", ProductoCreateView.as_view(), name="producto-create"),
    path("<int:pk>/", ProductoDetailView.as_view(), name="producto-detail"),
    path("<int:pk>/editar/", ProductoUpdateView.as_view(), name="producto-update"),
    path(
        "<int:pk>/editar-parcial/",
        ProductoPartialUpdateView.as_view(),
        name="producto-partial-update",
    ),
    path("<int:pk>/eliminar/", ProductoDeleteView.as_view(), name="producto-delete"),
]

carrito_patterns = [
    path("", CarritoDetailView.as_view(), name="carrito-detail"),
    path("items/", AddItemCarritoView.as_view(), name="carrito-add"),
    path("items/cantidad/", UpdateCantidadCarritoView.as_view(), name="carrito-update-cantidad"),
    path("items/quitar/", RemoveItemCarritoView.as_view(), name="carrito-remove"),
    path("vaciar/", ClearCarritoView.as_view(), name="carrito-clear"),
]

ordenes_patterns = [
    path("", OrdenListView.as_view(), name="ordenes-list"),
    path("<int:pk>/", OrdenDetailView.as_view(), name="ordenes-detail"),
]

envios_patterns = [
    path("", EnvioListCreateView.as_view(), name="envios-list-create"),
    path("<int:pk>/", EnvioDetailView.as_view(), name="envios-detail"),
]

urlpatterns = [
    path("productos/", include((productos_patterns, "productos"))),
    path("carrito/", include((carrito_patterns, "carrito"))),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("ordenes/", include((ordenes_patterns, "ordenes"))),
    path("envios/", include((envios_patterns, "envios"))),
    path("pagos/", include("apps.pagos.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("descuentos/", include("apps.descuentos.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("notificaciones/", include("apps.notificaciones.urls")),
    path("auth/", include("apps.auth_api.urls")),
]

from django.urls import path
from carrito.views import (
    CarritoDetailView,
    AddItemCarritoView,
    RemoveItemCarritoView,
    UpdateCantidadCarritoView,
    ClearCarritoView,
    CheckoutView,
)

urlpatterns = [
    path('carrito/', CarritoDetailView.as_view(), name='carrito-detail'),
    path('carrito/add/', AddItemCarritoView.as_view(), name='carrito-add'),
    path('carrito/remove/', RemoveItemCarritoView.as_view(), name='carrito-remove'),
    path('carrito/update-cantidad/', UpdateCantidadCarritoView.as_view(), name='carrito-update-cantidad'),
    path('carrito/clear/', ClearCarritoView.as_view(), name='carrito-clear'),
    path('carrito/checkout/', CheckoutView.as_view(), name='carrito-checkout'),
]

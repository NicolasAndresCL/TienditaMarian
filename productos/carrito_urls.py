from django.urls import path
from rest_framework.routers import DefaultRouter
from .carrito_views import CarritoViewSet, CheckoutViewSet, OrdenListView, OrdenDetailView, UpdateCantidadCarritoView

carrito_list = CarritoViewSet.as_view({'get': 'list'})
carrito_add = CarritoViewSet.as_view({'post': 'add'})
carrito_remove = CarritoViewSet.as_view({'post': 'remove'})
carrito_clear = CarritoViewSet.as_view({'post': 'clear'})
checkout = CheckoutViewSet.as_view({'post': 'create'})

urlpatterns = [
    path('carrito/', carrito_list, name='carrito-list'),
    path('carrito/add/', carrito_add, name='carrito-add'),
    path('carrito/remove/', carrito_remove, name='carrito-remove'),
    path('carrito/clear/', carrito_clear, name='carrito-clear'),
    path('checkout/', checkout, name='checkout'),
    path('ordenes/', OrdenListView.as_view(), name='ordenes-list'),
    path('ordenes/<int:pk>/', OrdenDetailView.as_view(), name='ordenes-detail'),
    path('carrito/update-cantidad/', UpdateCantidadCarritoView.as_view(), name='carrito-update-cantidad'),
]

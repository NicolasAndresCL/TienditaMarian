from django.test import TestCase
from apps.carrito.models import Carrito, ItemCarrito
from django.contrib.auth import get_user_model
from apps.productos.models import Producto
from apps.orden.models import Orden, ItemOrden

class CarritoOrdenTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='test', password='1234', email='test@mail.com')
        self.producto = Producto.objects.create(nombre='Test', descripcion='desc', precio=10, stock=5)
        self.carrito = Carrito.objects.create(usuario=self.user)

    def test_agregar_item_carrito(self):
        item = ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto, cantidad=2)
        self.assertEqual(item.cantidad, 2)
        self.assertEqual(self.carrito.items.count(), 1)

    def test_checkout_crea_orden(self):
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto, cantidad=2)
        total = self.producto.precio * 2
        orden = Orden.objects.create(usuario=self.user, total=total)
        ItemOrden.objects.create(orden=orden, producto=self.producto, cantidad=2, precio=self.producto.precio)
        self.assertEqual(orden.items.count(), 1)
        self.assertEqual(orden.total, total)
from django.test import TestCase
from apps.carrito.models import Carrito, ItemCarrito
from django.contrib.auth import get_user_model
from apps.productos.models import Producto
from apps.orden.models import Orden

User = get_user_model()

class CarritoOrdenTestCase(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="testuser",
            password="12345",
            email="testuser@example.com"
        )
        self.carrito = Carrito.objects.create(usuario=self.usuario)
        self.producto = Producto.objects.create(nombre="Test Producto", precio=1000, stock=10)
    
    def test_email_enviado_al_crear_orden(self):
        from django.core import mail
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto, cantidad=1)
        orden = Orden.objects.create(usuario=self.usuario, total=1000)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('Gracias por tu compra', mail.outbox[0].subject)
        
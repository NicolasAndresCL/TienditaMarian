from django.test import TestCase
from apps.carrito.models import Carrito, ItemCarrito
from django.contrib.auth import get_user_model
from apps.productos.models import Producto
from apps.orden.models import Orden, ItemOrden

class CarritoOrdenTestCase(TestCase):

    def test_email_enviado_al_crear_orden(self):
        from django.core import mail
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto, cantidad=1)
        orden = Orden.objects.create(usuario=self.user, total=10)
        self.carrito = Carrito.objects.create(usuario=self.usuario)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Gracias por tu compra', mail.outbox[0].subject)
        
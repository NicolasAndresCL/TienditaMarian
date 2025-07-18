from django.test import TestCase
from carrito.models import Carrito, ItemCarrito
from django.contrib.auth import get_user_model
from productos.models import Producto
from orden.models import Orden, ItemOrden

class CarritoOrdenTestCase(TestCase):

    def test_email_enviado_al_crear_orden(self):
        from django.core import mail
        ItemCarrito.objects.create(carrito=self.carrito, producto=self.producto, cantidad=1)
        orden = Orden.objects.create(usuario=self.user, total=10)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Gracias por tu compra', mail.outbox[0].subject)

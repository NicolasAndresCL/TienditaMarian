from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.orden.models import Orden
from .models import Pago

User = get_user_model()

class PagoModelTest(TestCase):
    def test_crear_pago(self):
        user = User.objects.create_user(username='testuser', password='12345')
        orden = Orden.objects.create(usuario=user, total=100)
        pago = Pago.objects.create(usuario=user, orden=orden, monto=100, metodo='stripe')
        self.assertEqual(pago.estado, 'pendiente')

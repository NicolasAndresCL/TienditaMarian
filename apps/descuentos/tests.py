from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Descuento
from datetime import date

User = get_user_model()

class DescuentoModelTest(TestCase):
    def test_crear_descuento_porcentaje(self):
        user = User.objects.create_user(username='testuser', password='12345')
        descuento = Descuento.objects.create(
            nombre='Descuento de prueba',
            tipo='porcentaje',
            valor=15.00,
            activo=True,
            fecha_inicio=date.today(),
            fecha_fin=date.today(),
            usuario=user
        )
        self.assertEqual(descuento.tipo, 'porcentaje')
        self.assertTrue(descuento.activo)
        self.assertEqual(str(descuento), 'Descuento de prueba (porcentaje - 15.00)')

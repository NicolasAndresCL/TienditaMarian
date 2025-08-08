from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import AnalyticsEvent

User = get_user_model()

class AnalyticsEventModelTest(TestCase):
    def test_crear_evento(self):
        user = User.objects.create_user(username='analyst', password='12345')
        evento = AnalyticsEvent.objects.create(
            tipo_evento='view',
            usuario=user,
            metadata={'producto_id': 1}
        )
        self.assertEqual(evento.tipo_evento, 'view')
        self.assertEqual(evento.metadata['producto_id'], 1)
        self.assertIsNotNone(evento.timestamp)

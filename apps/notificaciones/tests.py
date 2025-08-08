from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Notificacion

User = get_user_model()

class NotificacionModelTest(TestCase):
    def test_crear_notificacion(self):
        user = User.objects.create_user(username='testuser', password='12345')
        noti = Notificacion.objects.create(
            usuario=user,
            tipo='email',
            asunto='Confirmación de orden',
            mensaje='Tu orden ha sido confirmada.',
            enviada=False
        )
        self.assertFalse(noti.enviada)
        self.assertEqual(str(noti), f'Notificación {noti.id} - email - Pendiente')

from apps.orden.models import Orden

class NotificacionSignalTest(TestCase):
    def test_signal_crea_notificacion(self):
        user = User.objects.create_user(username='signaluser', password='12345')
        orden = Orden.objects.create(usuario=user, estado='pendiente')
        notificaciones = Notificacion.objects.filter(usuario=user)
        self.assertEqual(notificaciones.count(), 1)
        self.assertIn('Nueva orden creada', notificaciones.first().asunto)

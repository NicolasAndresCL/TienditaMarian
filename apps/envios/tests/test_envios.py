from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.orden.models import Orden
from .models import Envio

User = get_user_model()

class EnvioModelTest(TestCase):
    def test_crear_envio(self):
        user = User.objects.create_user(username='testuser', password='12345')
        orden = Orden.objects.create(usuario=user, total=150)
        envio = Envio.objects.create(
            usuario=user,
            orden=orden,
            direccion='Calle Falsa 123',
            ciudad='Rancagua',
            codigo_postal='1234567',
            estado='pendiente'
        )
        self.assertEqual(envio.estado, 'pendiente')
        self.assertEqual(str(envio), f'Envio {envio.id} - pendiente')

from rest_framework.test import APIClient
from rest_framework import status

class EnvioViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.force_authenticate(user=self.user)
        self.orden = Orden.objects.create(usuario=self.user, total=150)
        self.envio = Envio.objects.create(
            usuario=self.user,
            orden=self.orden,
            direccion='Calle Falsa 123',
            ciudad='Rancagua',
            codigo_postal='1234567',
            estado='pendiente'
        )

    def test_retrieve_envio(self):
        response = self.client.get(f'/api/envios/{self.envio.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'pendiente')

    def test_update_envio(self):
        response = self.client.put(f'/api/envios/{self.envio.id}/', {
            'usuario': self.user.id,
            'orden': self.orden.id,
            'direccion': 'Nueva Dirección 456',
            'ciudad': 'Rancagua',
            'codigo_postal': '7654321',
            'estado': 'enviado'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'enviado')

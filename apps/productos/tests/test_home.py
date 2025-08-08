from django.test import TestCase, Client
from django.urls import reverse
from apps.productos.models import Producto

class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        Producto.objects.create(nombre="Test", descripcion="desc", precio=1000, stock=1)

    def test_home_status_code(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

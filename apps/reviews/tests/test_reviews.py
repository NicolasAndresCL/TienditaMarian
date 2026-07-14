from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.productos.models import Producto
from .models import Review

User = get_user_model()

class ReviewModelTest(TestCase):
    def test_crear_review(self):
        user = User.objects.create_user(username='reviewer', password='12345')
        producto = Producto.objects.create(nombre='Producto Test', precio=100, stock=10)
        review = Review.objects.create(
            producto=producto,
            usuario=user,
            comentario='Muy buen producto',
            calificacion=5
        )
        self.assertEqual(review.calificacion, 5)
        self.assertEqual(str(review), f'Review {review.id} - 5⭐')

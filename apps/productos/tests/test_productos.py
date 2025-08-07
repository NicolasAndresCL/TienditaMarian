from django.test import TestCase
from productos.models import Producto
from decimal import Decimal

class ProductoModelTest(TestCase):
    def setUp(self):
        self.producto = Producto.objects.create(
            nombre="Carrito Didáctico Aprendizaje",
            descripcion="Un carrito didáctico ideal para el desarrollo de los niños.",
            precio=Decimal('3000.00'),
            stock=10
        )

    def test_producto_creation(self):
        producto_guardado = Producto.objects.get(nombre="Carrito Didáctico Aprendizaje")
        self.assertEqual(producto_guardado.nombre, "Carrito Didáctico Aprendizaje")
        self.assertEqual(producto_guardado.descripcion, "Un carrito didáctico ideal para el desarrollo de los niños.")
        self.assertEqual(producto_guardado.precio, Decimal('3000.00'))
        self.assertEqual(producto_guardado.stock, 10)
        self.assertIsNotNone(producto_guardado.creado)
        self.assertFalse(producto_guardado.image)

    def test_str_representation(self):
        """
        Verifica que el método __str__ devuelve el nombre del producto.
        """
        self.assertEqual(str(self.producto), "Carrito Didáctico Aprendizaje")

    def test_precio_decimal_places(self):
        """
        Verifica que el campo precio maneja correctamente los decimales.
        """
        producto_con_decimal = Producto.objects.create(
            nombre="Muñeca de Trapo",
            descripcion="Muñeca artesanal",
            precio=Decimal('25.50'),
            stock=5
        )
        self.assertEqual(producto_con_decimal.precio, Decimal('25.50'))

    def test_stock_non_negative(self):
        """
        Verifica que el stock puede ser cero o positivo.
        (Aunque Django no impone esto, es una buena práctica de testeo de lógica de negocio)
        """
        producto_sin_stock = Producto.objects.create(
            nombre="Pelota",
            descripcion="Pelota de fútbol",
            precio=Decimal('10.00'),
            stock=0
        )
        self.assertEqual(producto_sin_stock.stock, 0)
        # Puedes añadir un test para stock negativo si tu lógica de validación lo permite
        # o si quieres asegurar que el modelo no lo permite (lo cual requeriría validación en el modelo/serializer)

    def test_image_field_optional(self):
        """
        Verifica que el campo image es opcional y puede ser nulo o vacío.
        """
        # Producto creado en setUp ya tiene image=None
        # CORRECCIÓN AQUÍ: Comprueba que la imagen es "falsa" (no tiene un archivo asociado)
        self.assertFalse(self.producto.image)

        # Crea un producto con una imagen (simulada)
        producto_con_imagen = Producto.objects.create(
            nombre="Libro de Cuentos",
            descripcion="Cuentos infantiles",
            precio=Decimal('15.00'),
            stock=20,
            image='productos/libro.jpg' # En un test, puedes simular la ruta
        )
        self.assertEqual(producto_con_imagen.image.name, 'productos/libro.jpg')


import csv, os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from apps.productos.models import Producto

class Command(BaseCommand):
    help = 'Carga productos desde CSV con imágenes asociadas'

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(settings.BASE_DIR, 'apps/productos/fixtures/productos.csv')
        image_dir = os.path.join(settings.MEDIA_ROOT, 'productos/images')

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                producto, created = Producto.objects.get_or_create(
                    nombre=row['nombre'],
                    defaults={
                        'descripcion': row['descripcion'],
                        'precio': row['precio'],
                        'stock': row['stock']
                    }
                )
                if created:
                    image_path = os.path.join(image_dir, row['image'])
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as img_file:
                            producto.image.save(row['image'], File(img_file), save=True)
                    self.stdout.write(self.style.SUCCESS(f"✔ Producto creado: {producto.nombre}"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠ Producto ya existía: {producto.nombre}"))

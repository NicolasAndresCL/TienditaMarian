"""Siembra el catálogo de demostración desde un CSV con sus imágenes."""

import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.productos.models import Producto

# Coincide con el `upload_to` de Producto.image: por eso las fotos del catálogo
# se pueden referenciar donde ya están, sin copiarlas.
RUTA_IMAGENES = 'productos/images'


class Command(BaseCommand):
    help = 'Carga productos desde CSV con imágenes asociadas'

    def handle(self, *args, **kwargs):
        csv_path = Path(settings.BASE_DIR) / 'apps' / 'productos' / 'fixtures' / 'productos.csv'
        image_dir = Path(settings.MEDIA_ROOT) / RUTA_IMAGENES

        creados = existentes = sin_imagen = 0

        with csv_path.open(newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                producto, created = Producto.objects.get_or_create(
                    nombre=row['nombre'],
                    defaults={
                        'descripcion': row['descripcion'],
                        'precio': row['precio'],
                        'stock': row['stock'],
                    },
                )

                if not created:
                    existentes += 1
                    self.stdout.write(self.style.WARNING(f"⚠ Producto ya existía: {producto.nombre}"))
                    continue

                creados += 1
                if not self._adjuntar_imagen(producto, image_dir / row['image']):
                    sin_imagen += 1

                self.stdout.write(self.style.SUCCESS(f"✔ Producto creado: {producto.nombre}"))

        self.stdout.write(f"\nCreados: {creados} · Ya existían: {existentes}")

        if sin_imagen:
            # Antes esto pasaba callado: si el nombre del CSV no coincidía con el
            # archivo real (o el media no estaba montado en el contenedor), el
            # producto nacía sin foto y nadie se enteraba hasta ver la tienda.
            self.stdout.write(
                self.style.ERROR(
                    f"✖ {sin_imagen} producto(s) quedaron SIN IMAGEN. "
                    f"Revisá que los nombres del CSV existan en {image_dir}"
                )
            )

    def _adjuntar_imagen(self, producto: Producto, ruta: Path) -> bool:
        """Asocia la foto al producto. Devuelve False —avisando— si no está."""
        if not ruta.exists():
            self.stdout.write(self.style.ERROR(f"  ✖ Imagen no encontrada: {ruta.name}"))
            return False

        # Se apunta al archivo que YA está en el media, no se copia. Antes esto
        # era `producto.image.save(nombre, File(...))`, que copia el contenido: y
        # como el destino existía, Django le agregaba un sufijo aleatorio
        # (`BugsBunny_LHlNKBd.jpeg`). Cada corrida del comando dejaba una tanda
        # nueva de duplicados en el repo.
        producto.image.name = f"{RUTA_IMAGENES}/{ruta.name}"
        producto.save(update_fields=['image'])

        return True

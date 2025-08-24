import os
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File as DjangoFile
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.marian_loader.models import HitoCarga
from apps.marian_loader.services import carga_service

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Carga un CSV de productos desde línea de comandos.\n"
        "Ejemplo: python manage.py load_csv /ruta/a/productos.csv [--user-id 3]"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
            help="Ruta al archivo CSV que se importará."
        )
        parser.add_argument(
            "--user-id",
            type=int,
            dest="user_id",
            help="ID del usuario que realiza la carga (opcional)."
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        user_id = options.get("user_id")

        # Verificar existencia del archivo
        if not os.path.isfile(csv_path):
            raise CommandError(f"Archivo no encontrado: {csv_path}")

        # Obtener usuario (si se proporcionó)
        usuario = None
        if user_id:
            try:
                usuario = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise CommandError(f"No existe usuario con ID {user_id}")

        # Crear el HitoCarga en estado 'in_progress'
        nombre_archivo = os.path.basename(csv_path)
        hito = HitoCarga.objects.create(
            usuario=usuario,
            archivo=nombre_archivo,
            status=HitoCarga.IN_PROGRESS,
            fecha_inicio=timezone.now()
        )
        self.stdout.write(self.style.NOTICE(
            f"[Hito #{hito.pk}] Iniciando importación de '{nombre_archivo}'"
        ))

        try:
            # Reabrir el archivo para DjangoFile
            with open(csv_path, "rb") as f:
                django_file = DjangoFile(f, name=nombre_archivo)
                carga_service.ejecutar_import(hito, django_file)

            # Mostrar resumen
            estado = hito.get_status_display()
            self.stdout.write(self.style.SUCCESS(
                f"[Hito #{hito.pk}] Importación finalizada: {estado}\n"
                f"  Total: {hito.total}  |  "
                f"Éxitos: {hito.exitosos}  |  "
                f"Fallidos: {hito.fallidos}"
            ))
            self.stdout.write(f"Reporte disponible en hito.reporte (Markdown)")

        except Exception as e:
            # Si algo inesperado ocurre, el servicio ya actualizó el hito
            self.stderr.write(self.style.ERROR(
                f"[Hito #{hito.pk}] Error inesperado: {e}"
            ))
            raise


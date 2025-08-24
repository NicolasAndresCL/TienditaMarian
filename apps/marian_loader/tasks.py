import os
from celery import shared_task
from django.core.files.base import File

from apps.marian_loader.models import HitoCarga
from apps.marian_loader.services import carga_service


@shared_task(bind=True)
def ejecutar_import_async(self, hito_id: int, file_path: str) -> None:
    """
    Tarea Celery que reabre el CSV desde disco y dispara la importación.
    """
    hito = HitoCarga.objects.get(pk=hito_id)
    try:
        with open(file_path, 'rb') as f:
            django_file = File(f)
            carga_service.ejecutar_import(hito, django_file)
    finally:
        # Limpiar archivo si ya no es necesario
        try:
            os.remove(file_path)
        except OSError:
            pass

import traceback
from django.db import transaction
from django.utils import timezone

from .models import HitoCarga, DetalleCarga
from .importer import importar_csv
from .exporter import generar_markdown
from .exceptions import InvalidRowError


class CargaService:
    """
    Orquesta todo el flujo de importación:
      1. Lee y valida el CSV (importer.importar_csv)
      2. Persiste DetalleCarga (bulk_create)
      3. Actualiza HitoCarga (status, conteo, reporte)
      4. Genera un reporte en Markdown (exporter.generar_markdown)
    """

    def ejecutar_import(self, hito: HitoCarga, archivo) -> None:
        # Marcamos en progreso
        hito.status = HitoCarga.IN_PROGRESS
        hito.save(update_fields=['status'])

        try:
            # 1) Importar y validar filas
            #    devuelve List[dict] con keys: fila, datos, errores, producto (instancia o None)
            detalles = importar_csv(archivo)

            exitosos = sum(1 for d in detalles if not d['errores'])
            fallidos = len(detalles) - exitosos

            # 2) Construir instancias DetalleCarga
            detalle_objs = [
                DetalleCarga(
                    hito=hito,
                    fila=d['fila'],
                    datos=d['datos'],
                    errores=d['errores'],
                    producto=d.get('producto')
                )
                for d in detalles
            ]

            # 3) Persistir todo en una transacción
            with transaction.atomic():
                DetalleCarga.objects.bulk_create(detalle_objs)

                # 4) Actualizar hito con métricas y estado final
                hito.total = len(detalles)
                hito.exitosos = exitosos
                hito.fallidos = fallidos
                hito.status = (
                    HitoCarga.SUCCESS if fallidos == 0 else HitoCarga.FAILED
                )
                hito.fecha_fin = timezone.now()

                # 5) Generar reporte Markdown con resumen y errores
                hito.reporte = generar_markdown(hito, detalles)
                hito.save()

        except InvalidRowError as ire:
            # Error controlado en validación de filas
            hito.status = HitoCarga.FAILED
            hito.fecha_fin = timezone.now()
            hito.reporte = f"Validación fallida: {str(ire)}"
            hito.save()

        except Exception:
            # Error inesperado: guardamos stacktrace en el reporte
            trace = traceback.format_exc()
            hito.status = HitoCarga.FAILED
            hito.fecha_fin = timezone.now()
            hito.reporte = (
                "Error inesperado durante la importación:\n\n"
                f"```\n{trace}\n```"
            )
            hito.save()


# Instancia lista para usar en views o tasks
carga_service = CargaService()

from django.db import models
from django.conf import settings


class HitoCarga(models.Model):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    SUCCESS = 'success'
    FAILED = 'failed'

    STATUS_CHOICES = [
        (PENDING, 'Pendiente'),
        (IN_PROGRESS, 'En progreso'),
        (SUCCESS, 'Éxito'),
        (FAILED, 'Fallido'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario'
    )
    fecha_inicio = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de inicio'
    )
    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de fin'
    )
    total = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de filas'
    )
    exitosos = models.PositiveIntegerField(
        default=0,
        verbose_name='Filas exitosas'
    )
    fallidos = models.PositiveIntegerField(
        default=0,
        verbose_name='Filas fallidas'
    )
    archivo = models.CharField(
        max_length=255,
        verbose_name='Nombre de archivo'
    )
    reporte = models.TextField(
        blank=True,
        verbose_name='Reporte de errores (Markdown o JSON)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        verbose_name='Estado'
    )

    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name = 'Hito de Carga'
        verbose_name_plural = 'Hitos de Carga'

    def __str__(self):
        return f"HitoCarga #{self.pk} – {self.usuario or 'Sistema'} – {self.get_status_display()}"


class DetalleCarga(models.Model):
    hito = models.ForeignKey(
        HitoCarga,
        related_name='detalles',
        on_delete=models.CASCADE,
        verbose_name='Hito de carga'
    )
    fila = models.PositiveIntegerField(verbose_name='Número de fila')
    datos = models.JSONField(verbose_name='Datos de la fila')
    errores = models.JSONField(verbose_name='Errores detectados')
    producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Producto creado'
    )

    class Meta:
        ordering = ['fila']
        verbose_name = 'Detalle de Carga'
        verbose_name_plural = 'Detalles de Carga'

    def __str__(self):
        err_count = len(self.errores) if isinstance(self.errores, (list, dict)) else '–'
        return f"Fila {self.fila} – Errores: {err_count}"

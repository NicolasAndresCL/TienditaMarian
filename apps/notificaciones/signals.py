from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.orden.models import Orden
from .models import Notificacion

@receiver(post_save, sender=Orden)
def crear_notificacion_orden(sender, instance, created, **kwargs):
    if created:
        estado = 'Pagada' if instance.pagado else 'Pendiente'
        mensaje = f"Se ha creado la orden #{instance.id} con estado {estado}."
        Notificacion.objects.create(
            usuario=instance.usuario,
            tipo='email',
            asunto='Nueva orden creada',
            mensaje=mensaje,
            enviada=False
        )
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail

from .models import ItemOrden

@receiver(post_save, sender=ItemOrden)
def enviar_email_nueva_orden(sender, instance, created, **kwargs):
    if created:
        usuario = instance.usuario
        if usuario.email:
            send_mail(
                subject='¡Gracias por tu compra!',
                message=f'Se ha creado tu orden #{instance.id} por un total de ${instance.total}.',
                from_email='no-reply@tienditademarian.com',
                recipient_list=[usuario.email],
                fail_silently=True
            )

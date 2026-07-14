from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notificaciones'
    verbose_name = 'Notificaciones'

    # La notificación de una orden nueva ya no se crea desde una señal post_save
    # de esta app: es un suscriptor del evento ORDEN_CREADA, registrado en
    # apps/orden/subscribers.py junto con los demás efectos de una compra.

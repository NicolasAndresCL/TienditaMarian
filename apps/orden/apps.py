from django.apps import AppConfig


class OrdenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orden'
    verbose_name = 'Órdenes'

    def ready(self):
        # Los efectos de una orden (correo, notificación, envío) se registran
        # como suscriptores explícitos del despachador, en vez de esconderse en
        # señales post_save repartidas por varias apps.
        from apps.orden.subscribers import registrar_suscriptores

        registrar_suscriptores()

from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notificaciones'
    verbose_name = 'Notificaciones'

    def ready(self):
        # El import es lo que registra los receivers decorados con @receiver.
        # Parece "sin usar", pero no lo es: el `noqa` impide que un linter lo
        # elimine y deje las señales silenciosamente desconectadas.
        import apps.notificaciones.signals  # noqa: F401

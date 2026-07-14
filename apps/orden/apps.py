from django.apps import AppConfig


class OrdenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orden'
    verbose_name = 'Órdenes'

    def ready(self):
        # El import es lo que registra los receivers decorados con @receiver.
        # Parece "sin usar", pero no lo es: el `noqa` impide que un linter lo
        # elimine y deje las señales silenciosamente desconectadas.
        import apps.orden.signals  # noqa: F401

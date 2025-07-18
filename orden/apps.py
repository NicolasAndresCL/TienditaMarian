from django.apps import AppConfig



class OrdenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orden'

    def ready(self):
        import orden.signals
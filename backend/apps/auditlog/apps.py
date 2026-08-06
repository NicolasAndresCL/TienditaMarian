from django.apps import AppConfig


class AuditlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.auditlog'
    verbose_name = 'Auditoría'

    def ready(self):
        from apps.auditlog.signals import conectar_signals

        conectar_signals()

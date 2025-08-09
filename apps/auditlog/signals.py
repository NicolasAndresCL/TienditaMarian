from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.auditlog.utils import log_action

IGNORED_MODELS = ['AuditLog', 'Migration', 'ContentType', 'LogEntry']

@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    model_name = instance.__class__.__name__
    if sender._meta.app_label != 'auditlog' and model_name not in IGNORED_MODELS:
        action = 'create' if created else 'update'
        log_action(instance, action)

@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    model_name = instance.__class__.__name__
    if sender._meta.app_label != 'auditlog' and model_name not in IGNORED_MODELS:
        log_action(instance, 'delete')

from django.forms.models import model_to_dict
from datetime import datetime
from apps.auditlog.models import AuditLog
from decimal import Decimal

def serialize_value(value):
    """Serializa un valor para que sea compatible con JSON"""
    if isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, Decimal):  # Agregué esto para manejar Decimals
        return float(value)
    return value

def log_action(instance, action, user=None):
    """Registra una acción en el log de auditoría"""
    print(f"AuditLog triggered for {instance} with action {action}")
    serialized_data = {k: serialize_value(v) for k, v in model_to_dict(instance, exclude=['image']).items()}

    AuditLog.objects.create(
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        action=action,
        user=user,
        changes=serialized_data
    )
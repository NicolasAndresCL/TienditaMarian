"""Serialización y escritura de entradas de auditoría."""

from __future__ import annotations

import json
import logging
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.forms.models import model_to_dict

from apps.auditlog.models import AuditLog
from core.middleware import get_usuario_actual

logger = logging.getLogger(__name__)

# Nunca deben quedar registrados en la bitácora. La versión anterior serializaba
# el modelo entero, así que cada `save()` de un User escribía el hash de su
# contraseña dentro del JSON de la tabla de auditoría.
CAMPOS_SENSIBLES = frozenset(
    {"password", "token", "secret", "api_key", "access", "refresh", "clave"}
)


def _es_sensible(campo: str) -> bool:
    return any(marca in campo.lower() for marca in CAMPOS_SENSIBLES)


def serializar_instancia(instance: models.Model) -> dict[str, Any]:
    """Convierte una instancia en un dict apto para un JSONField.

    `DjangoJSONEncoder` ya sabe manejar date, datetime, Decimal y UUID. La
    versión anterior los convertía a mano y se olvidó de `date`, así que
    guardar cualquier modelo con un DateField (por ejemplo `Descuento`)
    reventaba con TypeError.
    """
    datos = {
        campo: valor
        for campo, valor in model_to_dict(instance).items()
        if not _es_sensible(campo)
    }
    # Ida y vuelta por JSON: normaliza FileField, Decimal, date y cualquier otro
    # tipo que el JSONField rechazaría, y falla aquí —donde sí lo capturamos—
    # en vez de al escribir en la base.
    return json.loads(json.dumps(datos, cls=DjangoJSONEncoder, default=str))


def log_action(instance: models.Model, action: str) -> AuditLog | None:
    """Registra una acción en la bitácora.

    Nunca lanza: una auditoría caída no puede tumbar una venta (skill §2.2). Si
    algo falla se deja constancia en el log de la aplicación y la operación de
    negocio sigue su curso.
    """
    try:
        return AuditLog.objects.create(
            model_name=instance.__class__.__name__,
            object_id=str(instance.pk),
            action=action,
            user=get_usuario_actual(),
            changes=serializar_instancia(instance),
        )
    except Exception:
        logger.exception(
            "No se pudo auditar %s(pk=%s) accion=%s",
            instance.__class__.__name__,
            instance.pk,
            action,
        )
        return None

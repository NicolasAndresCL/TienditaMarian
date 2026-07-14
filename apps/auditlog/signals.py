"""Conexión de la auditoría a los modelos de negocio.

La versión anterior escuchaba `post_save` y `post_delete` **globales** y luego
descartaba lo que no le servía con una lista negra de cuatro nombres. Eso
implicaba auditar todo lo demás que Django guardase: `User` (con su hash de
contraseña), `Session`, los tokens JWT de la blacklist... Aquí se invierte a
lista blanca: se audita lo que está declarado, y nada más.
"""

from __future__ import annotations

import logging

from django.apps import apps as django_apps
from django.db.models.signals import post_delete, post_save

from apps.auditlog.utils import log_action

logger = logging.getLogger(__name__)

# Modelos de negocio cuya trazabilidad importa: qué se vendió, a qué precio, a
# dónde se envió y quién lo tocó.
MODELOS_AUDITADOS: tuple[str, ...] = (
    "productos.Producto",
    "orden.Orden",
    "orden.ItemOrden",
    "pagos.Pago",
    "envios.Envio",
    "descuentos.Descuento",
)


def _on_post_save(sender, instance, created, **kwargs) -> None:
    log_action(instance, "create" if created else "update")


def _on_post_delete(sender, instance, **kwargs) -> None:
    log_action(instance, "delete")


def conectar_signals() -> None:
    """Engancha la auditoría a cada modelo de la lista blanca.

    `dispatch_uid` hace la conexión idempotente: si `ready()` corre dos veces
    (ocurre con el autoreloader), no se duplican las entradas.
    """
    for etiqueta in MODELOS_AUDITADOS:
        try:
            modelo = django_apps.get_model(etiqueta)
        except LookupError:
            logger.warning("Modelo auditado inexistente, se omite: %s", etiqueta)
            continue

        post_save.connect(_on_post_save, sender=modelo, dispatch_uid=f"auditlog_save_{etiqueta}")
        post_delete.connect(
            _on_post_delete, sender=modelo, dispatch_uid=f"auditlog_delete_{etiqueta}"
        )

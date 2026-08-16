"""Efectos de los hechos de inventario.

`STOCK_AGOTADO` llevaba desde su creación emitiéndose al vacío: el checkout lo
anunciaba cada vez que una compra se caía por falta de stock y no había nadie
escuchando. Una venta perdida —justo el dato que a la tienda le sirve— no dejaba
rastro en ninguna parte.
"""

from __future__ import annotations

import logging

from django.contrib.auth import get_user_model

from apps.notificaciones.models import Notificacion
from apps.productos.models import Producto
from core.events import Evento, despachador

logger = logging.getLogger(__name__)


def avisar_venta_perdida(producto: Producto) -> None:
    """Avisa al personal de la tienda de que una compra se cayó por stock.

    Una notificación por cada persona de staff. Si no hay ninguna —una base
    recién creada, por ejemplo— no se crea nada y se deja constancia en el log:
    quedarse sin destinatarios no es un error.
    """
    destinatarios = list(get_user_model().objects.filter(is_staff=True, is_active=True))

    logger.warning(
        "Venta perdida por stock: producto=%s (id=%s) quedan=%s; avisando a %s del staff",
        producto.nombre,
        producto.pk,
        producto.stock,
        len(destinatarios),
    )

    if not destinatarios:
        return

    Notificacion.objects.bulk_create(
        [
            Notificacion(
                usuario=persona,
                tipo="email",
                asunto="Venta perdida por falta de stock",
                mensaje=(
                    f"Alguien intentó comprar «{producto.nombre}» y no alcanzó el "
                    f"stock (quedan {producto.stock}). Conviene reponerlo."
                ),
                enviada=False,
            )
            for persona in destinatarios
        ]
    )


def registrar_suscriptores() -> None:
    """Conecta los efectos. Se llama una vez, desde `ProductosConfig.ready()`."""
    despachador.suscribir(Evento.STOCK_AGOTADO, avisar_venta_perdida)

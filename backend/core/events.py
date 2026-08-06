"""Eventos de dominio con callbacks inyectables (skill §2.3).

El problema que resuelve: hoy, crear una `Orden` dispara tres efectos ocultos
—un correo desde `Orden.save()`, otro correo desde una señal `post_save`, y una
`Notificacion` desde otra señal—. Nada de eso es visible al leer el checkout, y
no hay forma de probar la regla de negocio sin que se dispare todo lo demás.

Aquí los efectos se **declaran** y se **inyectan**: el servicio anuncia "se creó
una orden" y no sabe quién escucha. En los tests se le inyecta un espía o
directamente nada.

Regla clave: un suscriptor que falla **no puede tumbar la operación**. Si el
servidor de correo está caído, la venta ya ocurrió y debe quedar registrada; el
fallo del correo se anota en el log y la vida sigue (skill §2.2 y §2.5).

    despachador = Despachador()
    despachador.suscribir(Evento.ORDEN_CREADA, enviar_correo_confirmacion)
    despachador.emitir(Evento.ORDEN_CREADA, orden)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)

Callback = Callable[..., Any]


class Evento(StrEnum):
    """Hechos del negocio. Nombrados en pasado: ya ocurrieron, no son órdenes."""

    ORDEN_CREADA = "orden_creada"
    ORDEN_PAGADA = "orden_pagada"
    STOCK_AGOTADO = "stock_agotado"


class Despachador:
    """Registro de suscriptores por evento."""

    def __init__(self) -> None:
        self._suscriptores: dict[Evento, list[Callback]] = defaultdict(list)

    def suscribir(self, evento: Evento, callback: Callback) -> None:
        if callback in self._suscriptores[evento]:
            return  # idempotente: registrar dos veces no duplica el efecto
        self._suscriptores[evento].append(callback)

    def desuscribir(self, evento: Evento, callback: Callback) -> None:
        if callback in self._suscriptores[evento]:
            self._suscriptores[evento].remove(callback)

    def suscriptores(self, evento: Evento) -> list[Callback]:
        return list(self._suscriptores[evento])

    def emitir(self, evento: Evento, *args: Any, **kwargs: Any) -> list[Exception]:
        """Notifica a todos los suscriptores. Nunca lanza.

        Devuelve los fallos para que quien llame decida (normalmente: ignorarlos,
        porque la operación de negocio ya se completó). Cada suscriptor va en su
        propio try: si el primero explota, los demás igual reciben el evento.
        """
        fallos: list[Exception] = []

        for callback in self._suscriptores[evento]:
            try:
                callback(*args, **kwargs)
            except Exception as exc:
                nombre = getattr(callback, "__name__", repr(callback))
                logger.exception("El suscriptor %s falló al procesar %s", nombre, evento.value)
                fallos.append(exc)

        return fallos


# Despachador de la aplicación. Los servicios lo usan por defecto y los tests
# pueden inyectar uno propio, vacío, para aislar la lógica de sus efectos.
despachador = Despachador()

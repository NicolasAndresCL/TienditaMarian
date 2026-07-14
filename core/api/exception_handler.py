"""Traducción de excepciones a respuestas HTTP.

Registrado en `REST_FRAMEWORK['EXCEPTION_HANDLER']`, es el único lugar del
proyecto que convierte un error en un `Response`. Las vistas ya no arman
`Response({'detail': ...}, status=400)` a mano.

Todos los errores salen con la misma forma, para que el frontend tenga un solo
contrato que interpretar:

    {"error": {"codigo": "stock_insuficiente",
               "mensaje": "No alcanza el stock de «Muñeca»: pediste 3 y quedan 2.",
               "detalle": {"producto": "Muñeca", "solicitado": 3, "disponible": 2}}}
"""

from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from core.exceptions import TienditaError

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Maneja los errores de negocio; delega el resto en DRF."""
    if isinstance(exc, TienditaError):
        return _respuesta_de_dominio(exc, context)

    if isinstance(exc, ObjectDoesNotExist) and not isinstance(exc, Http404):
        # Un .get() que no encuentra nada es un 404, no un 500.
        return Response(
            {"error": {"codigo": "no_encontrado", "mensaje": "El recurso no existe.", "detalle": {}}},
            status=status.HTTP_404_NOT_FOUND,
        )

    respuesta = drf_exception_handler(exc, context)
    if respuesta is None:
        # DRF no supo qué hacer: es un bug, no una regla de negocio. Se registra
        # con traceback y se deja que Django devuelva el 500; tragarlo aquí
        # escondería el problema (skill §2.5: fallar ruidosamente).
        logger.exception("Excepción no controlada en %s", context.get("view"))
        return None

    return _normalizar_respuesta_drf(respuesta, exc)


def _respuesta_de_dominio(exc: TienditaError, context: dict[str, Any]) -> Response:
    # Un error de negocio es esperable (stock que se acabó, cupón vencido): se
    # registra como warning, no como excepción — no hay nada que arreglar en el
    # código.
    logger.warning(
        "Regla de negocio rechazó la operación: codigo=%s vista=%s mensaje=%s",
        exc.codigo,
        context.get("view").__class__.__name__ if context.get("view") else "?",
        exc.mensaje,
    )
    return Response(
        {"error": {"codigo": exc.codigo, "mensaje": exc.mensaje, "detalle": exc.detalle()}},
        status=exc.http_status,
    )


def _normalizar_respuesta_drf(respuesta: Response, exc: Exception) -> Response:
    """Envuelve los errores propios de DRF en el mismo formato que los de dominio."""
    codigo = getattr(exc, "default_code", None) or "error_peticion"
    datos = respuesta.data

    if isinstance(datos, dict) and "detail" in datos:
        mensaje, detalle = str(datos["detail"]), {}
    elif isinstance(datos, dict):
        # Errores de validación de un serializer: {"campo": ["mensaje", ...]}.
        mensaje, detalle = "Los datos enviados no son válidos.", datos
    else:
        mensaje, detalle = "Los datos enviados no son válidos.", {"errores": datos}

    respuesta.data = {"error": {"codigo": codigo, "mensaje": mensaje, "detalle": detalle}}
    return respuesta

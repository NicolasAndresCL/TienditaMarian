"""Vistas de infraestructura."""

from django.db import connection
from django.http import HttpRequest, JsonResponse


def healthz(request: HttpRequest) -> JsonResponse:
    """Comprobación de vida para el orquestador y los monitores externos.

    No basta con responder 200: si la base de datos está caída, el contenedor
    está vivo pero la tienda no puede vender. Por eso se hace una consulta real.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:  # noqa: BLE001 — cualquier fallo aquí es "no estoy sano"
        return JsonResponse(
            {"status": "error", "base_de_datos": "caída", "detalle": str(exc)},
            status=503,
        )

    return JsonResponse({"status": "ok", "base_de_datos": "ok"})

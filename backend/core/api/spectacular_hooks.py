"""Hooks de drf-spectacular para la generación del esquema OpenAPI."""

from __future__ import annotations

# Prefijos que SÍ entran en el esquema público. Todo lo demás bajo /api/ son las
# rutas v0 deprecadas (strangler-fig): comparten vista y operationId con sus
# equivalentes v1, así que si se documentaran ambas, drf-spectacular emitiría
# decenas de warnings W001 por operationId duplicado — y `check --deploy
# --fail-level WARNING` las trata como fallo de build. La documentación pública
# muestra solo v1; las viejas responden pero no se publican.
PREFIJOS_PUBLICOS = ("/api/v1/",)


def excluir_rutas_legacy(endpoints, **kwargs):
    """Filtra el esquema para dejar únicamente los endpoints de /api/v1/.

    `endpoints` es una lista de tuplas (path, path_regex, method, callback).
    """
    return [
        (path, path_regex, method, callback)
        for (path, path_regex, method, callback) in endpoints
        if path.startswith(PREFIJOS_PUBLICOS)
    ]

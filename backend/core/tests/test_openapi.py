"""El esquema OpenAPI solo publica /api/v1/.

Regresión: las rutas v0 deprecadas comparten vista y operationId con las v1, así
que si se documentaran ambas, drf-spectacular emitía ~46 warnings W001 por
operationId duplicado y `check --deploy --fail-level WARNING` rompía el CI. El
preprocessing hook `excluir_rutas_legacy` deja solo v1; este test lo blinda.
"""

import pytest
from drf_spectacular.generators import SchemaGenerator


@pytest.fixture
def esquema():
    return SchemaGenerator().get_schema(request=None, public=True)


def test_el_esquema_solo_incluye_rutas_v1(esquema):
    rutas_api = [p for p in esquema["paths"] if p.startswith("/api/")]

    assert rutas_api, "el esquema debería tener rutas /api/"
    no_v1 = [p for p in rutas_api if not p.startswith("/api/v1/")]
    assert no_v1 == [], f"las rutas v0 no deben publicarse en el esquema: {no_v1}"


def test_el_esquema_publica_los_endpoints_clave_de_v1(esquema):
    paths = esquema["paths"]

    for esperado in ("/api/v1/productos/", "/api/v1/checkout/", "/api/v1/auth/token/"):
        assert esperado in paths, f"falta {esperado} en el esquema v1"


def test_no_hay_operationids_duplicados(esquema):
    ids = [
        op["operationId"]
        for metodos in esquema["paths"].values()
        for op in metodos.values()
        if isinstance(op, dict) and "operationId" in op
    ]

    duplicados = {i for i in ids if ids.count(i) > 1}
    assert not duplicados, f"operationId duplicados (causan W001): {duplicados}"

"""Contrato HTTP del carrito.

Los tests de errores del carrito que ya existían son **de servicio**
(`pytest.raises(CantidadInvalidaError)` sobre `CarritoService`), así que
comprobaban la regla de negocio pero no lo que la API responde de verdad. Con la
validación movida al serializer, la frontera HTTP necesita sus propios tests:
son los que fijan qué código de estado y qué cuerpo ve el frontend.
"""

import pytest


def _error(respuesta) -> dict:
    """El cuerpo de error que este proyecto garantiza en TODA la API."""
    return respuesta.json()["error"]


# ----------------------------------------------------- validación del cuerpo


@pytest.mark.django_db
def test_agregar_sin_producto_id_es_400_y_no_500(auth_client):
    """`data['producto_id']` llegó a lanzar KeyError → HTTP 500.

    Ahora lo rechaza el serializer: es un cuerpo mal formado, no un producto que
    no existe, así que es 400 y no 404.
    """
    respuesta = auth_client.post("/api/v1/carrito/items/", {}, format="json")

    assert respuesta.status_code == 400
    assert "producto_id" in _error(respuesta)["detalle"]


@pytest.mark.django_db
@pytest.mark.parametrize("cantidad", ["abc", 0, -3, 2.5, ""])
def test_agregar_con_una_cantidad_invalida_es_400(auth_client, producto, cantidad):
    """`int(request.data.get('cantidad'))` devolvía 500 ante "abc"."""
    respuesta = auth_client.post(
        "/api/v1/carrito/items/",
        {"producto_id": producto.id, "cantidad": cantidad},
        format="json",
    )

    assert respuesta.status_code == 400
    assert "cantidad" in _error(respuesta)["detalle"]


@pytest.mark.django_db
def test_agregar_sin_cantidad_asume_una_unidad(auth_client, producto):
    respuesta = auth_client.post(
        "/api/v1/carrito/items/", {"producto_id": producto.id}, format="json"
    )

    assert respuesta.status_code == 200
    assert respuesta.data["cantidad"] == 1


@pytest.mark.django_db
def test_un_producto_inexistente_sigue_siendo_404(auth_client):
    """El cuerpo es válido; lo que no existe es el recurso. Lo decide el servicio."""
    respuesta = auth_client.post(
        "/api/v1/carrito/items/", {"producto_id": 999999}, format="json"
    )

    assert respuesta.status_code == 404
    assert _error(respuesta)["codigo"] == "producto_no_encontrado"


@pytest.mark.django_db
def test_actualizar_sin_cantidad_es_400(auth_client, producto):
    """Antes reutilizaba el serializer de agregar, con `default=1`: un PATCH sin
    cantidad dejaba el ítem en 1 unidad sin que nadie lo hubiera pedido."""
    auth_client.post(
        "/api/v1/carrito/items/", {"producto_id": producto.id, "cantidad": 3}, format="json"
    )

    respuesta = auth_client.patch(
        "/api/v1/carrito/items/cantidad/", {"producto_id": producto.id}, format="json"
    )

    assert respuesta.status_code == 400
    assert "cantidad" in _error(respuesta)["detalle"]

    # Y sobre todo: no tocó el carrito.
    carrito = auth_client.get("/api/v1/carrito/")
    assert carrito.data["items"][0]["cantidad"] == 3


@pytest.mark.django_db
def test_quitar_sin_producto_id_es_400(auth_client):
    respuesta = auth_client.delete("/api/v1/carrito/items/quitar/", {}, format="json")

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_el_error_de_validacion_usa_el_formato_de_toda_la_api(auth_client):
    """Un error de DRF sale con la misma forma que uno de dominio.

    El frontend interpreta un solo contrato: `{error: {codigo, mensaje, detalle}}`.
    """
    respuesta = auth_client.post("/api/v1/carrito/items/", {}, format="json")

    cuerpo = _error(respuesta)
    assert set(cuerpo) == {"codigo", "mensaje", "detalle"}
    assert cuerpo["mensaje"]


@pytest.mark.django_db
def test_el_stock_insuficiente_sigue_siendo_409_con_su_detalle(auth_client, producto):
    """La validación del serializer no se traga los errores de negocio."""
    respuesta = auth_client.post(
        "/api/v1/carrito/items/",
        {"producto_id": producto.id, "cantidad": producto.stock + 1},
        format="json",
    )

    assert respuesta.status_code == 409
    cuerpo = _error(respuesta)
    assert cuerpo["codigo"] == "stock_insuficiente"
    # El frontend muestra "quedan N unidades" a partir de este dato.
    assert cuerpo["detalle"]["disponible"] == producto.stock


# ------------------------------------------------------------ consultas (N+1)


@pytest.mark.django_db
def test_ver_el_carrito_no_depende_del_numero_de_productos(
    auth_client, usuario, django_assert_num_queries
):
    """`GET /carrito/` costaba 4+2N consultas.

    Se comprueba la propiedad, no un número mágico: el coste con tres productos
    tiene que ser el MISMO que con uno. Un test con un número fijo se rompe con
    cualquier cambio inocuo del ORM y acaba ajustándose a ojo hasta que deja de
    proteger nada.
    """
    from apps.productos.models import Producto

    def medir(cuantos: int) -> int:
        auth_client.delete("/api/v1/carrito/vaciar/")
        for i in range(cuantos):
            p = Producto.objects.create(
                nombre=f"Juguete {cuantos}-{i}", descripcion="x", precio="1000.00", stock=50
            )
            auth_client.post(
                "/api/v1/carrito/items/", {"producto_id": p.id, "cantidad": 2}, format="json"
            )

        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as capturadas:
            respuesta = auth_client.get("/api/v1/carrito/")
        assert respuesta.status_code == 200
        assert len(respuesta.data["items"]) == cuantos
        return len(capturadas)

    con_uno = medir(1)
    con_tres = medir(3)

    assert con_uno == con_tres, (
        f"el carrito hace {con_uno} consultas con 1 producto y {con_tres} con 3: "
        "volvió el N+1"
    )

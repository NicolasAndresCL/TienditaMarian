"""Tests de las rutas: la v1 nueva, el healthcheck y la convivencia con la v0."""

from decimal import Decimal

import pytest

from apps.carrito.models import Carrito, ItemCarrito


@pytest.mark.django_db
def test_healthz_responde_ok(client):
    respuesta = client.get("/healthz/")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok", "base_de_datos": "ok"}


@pytest.mark.django_db
def test_la_vitrina_ya_no_cuelga_de_la_api(client, producto):
    """La home HTML vive en `/`, no dentro de `/api/productos/`."""
    assert client.get("/").status_code == 200


# ------------------------------------------------------------------ API v1


@pytest.mark.django_db
def test_v1_catalogo_publico(api_client, producto):
    respuesta = api_client.get("/api/v1/productos/")

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 1


@pytest.mark.django_db
def test_v1_detalle_de_producto(api_client, producto):
    assert api_client.get(f"/api/v1/productos/{producto.id}/").status_code == 200


@pytest.mark.django_db
def test_v1_un_cliente_no_administra_el_catalogo(auth_client, producto):
    respuesta = auth_client.patch(
        f"/api/v1/productos/{producto.id}/editar-parcial/", {"precio": "1.00"}, format="json"
    )

    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_v1_flujo_completo_de_compra(auth_client, usuario, producto):
    """Agregar al carrito y comprar, todo por las rutas nuevas."""
    agregado = auth_client.post(
        "/api/v1/carrito/items/", {"producto_id": producto.id, "cantidad": 2}, format="json"
    )
    assert agregado.status_code == 200

    carrito = auth_client.get("/api/v1/carrito/")
    assert carrito.status_code == 200
    assert Decimal(carrito.data["total"]) == Decimal("6000.00")

    orden = auth_client.post("/api/v1/checkout/", {}, format="json")
    assert orden.status_code == 201

    producto.refresh_from_db()
    assert producto.stock == 8

    historial = auth_client.get("/api/v1/ordenes/")
    assert historial.data["count"] == 1


@pytest.mark.django_db
def test_v1_actualizar_y_quitar_del_carrito(auth_client, usuario, producto):
    auth_client.post(
        "/api/v1/carrito/items/", {"producto_id": producto.id, "cantidad": 1}, format="json"
    )

    actualizado = auth_client.patch(
        "/api/v1/carrito/items/cantidad/",
        {"producto_id": producto.id, "cantidad": 5},
        format="json",
    )
    assert actualizado.status_code == 200
    assert actualizado.data["cantidad"] == 5

    quitado = auth_client.delete(
        "/api/v1/carrito/items/quitar/", {"producto_id": producto.id}, format="json"
    )
    assert quitado.status_code == 204
    assert not ItemCarrito.objects.filter(carrito__usuario=usuario).exists()


@pytest.mark.django_db
def test_v1_vaciar_carrito(auth_client, usuario, producto):
    carrito = Carrito.objects.create(usuario=usuario)
    ItemCarrito.objects.create(carrito=carrito, producto=producto, cantidad=1)

    respuesta = auth_client.delete("/api/v1/carrito/vaciar/")

    assert respuesta.status_code == 204
    assert carrito.items.count() == 0


@pytest.mark.django_db
def test_v1_auth(api_client):
    respuesta = api_client.post(
        "/api/v1/auth/register/",
        {
            "username": "nueva",
            "email": "nueva@ejemplo.com",
            "password": "Tiendita-2026-Segura",
            "password_confirm": "Tiendita-2026-Segura",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert "access" in respuesta.data["token"]


# ------------------------------------------------------------------ convivencia


@pytest.mark.django_db
def test_las_rutas_viejas_siguen_funcionando(auth_client, producto):
    """Strangler-fig: el frontend actual no se rompe mientras se migra."""
    assert auth_client.get("/api/productos/productos/").status_code == 200
    assert auth_client.get("/api/carrito/carrito/").status_code == 200
    assert auth_client.get("/api/orden/ordenes/").status_code == 200

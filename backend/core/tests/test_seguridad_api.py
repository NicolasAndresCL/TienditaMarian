"""Tests de autorización de la API — un test por agujero encontrado en la auditoría.

Todos estos fallaban contra el código original: la API pedía `IsAuthenticated`
(¿quién eres?) pero nunca comprobaba la propiedad del objeto (¿esto es tuyo?), y
los serializers con `fields = '__all__'` dejaban fijar el dueño desde el cuerpo
de la petición.

El escenario es siempre el mismo: `usuario` tiene datos, e `intruso` —una cuenta
recién registrada, como la de cualquier visitante— intenta llegar a ellos.
"""

from datetime import date
from decimal import Decimal

import pytest

from apps.descuentos.models import Descuento
from apps.envios.models import Envio
from apps.notificaciones.models import Notificacion
from apps.orden.models import Orden
from apps.pagos.models import Pago
from apps.reviews.models import Review


@pytest.fixture
def orden_ajena(db, usuario):
    return Orden.objects.create(usuario=usuario, total=Decimal("15000"))


@pytest.fixture
def envio_ajeno(db, usuario, orden_ajena):
    return Envio.objects.create(
        usuario=usuario,
        orden=orden_ajena,
        direccion="Av. Siempre Viva 742",
        ciudad="Rancagua",
        codigo_postal="2820000",
    )


@pytest.fixture
def pago_ajeno(db, usuario, orden_ajena):
    return Pago.objects.create(
        usuario=usuario, orden=orden_ajena, monto=Decimal("15000"), metodo="webpay"
    )


# ---------------------------------------------------------------- envíos
# El peor de todos: expone la dirección de domicilio de las clientas.


@pytest.mark.django_db
def test_un_intruso_no_puede_leer_el_envio_de_otro(otro_client, envio_ajeno):
    respuesta = otro_client.get(f"/api/envios/{envio_ajeno.id}/")

    assert respuesta.status_code == 404, "la dirección de otra clienta no puede ser legible"


@pytest.mark.django_db
def test_un_intruso_no_puede_editar_el_envio_de_otro(otro_client, envio_ajeno):
    respuesta = otro_client.patch(
        f"/api/envios/{envio_ajeno.id}/", {"direccion": "Mi casa 123"}, format="json"
    )

    assert respuesta.status_code == 404
    envio_ajeno.refresh_from_db()
    assert envio_ajeno.direccion == "Av. Siempre Viva 742"


@pytest.mark.django_db
def test_un_intruso_no_puede_borrar_el_envio_de_otro(otro_client, envio_ajeno):
    respuesta = otro_client.delete(f"/api/envios/{envio_ajeno.id}/")

    assert respuesta.status_code == 404
    assert Envio.objects.filter(pk=envio_ajeno.pk).exists()


@pytest.mark.django_db
def test_el_listado_de_envios_solo_muestra_los_propios(otro_client, envio_ajeno):
    respuesta = otro_client.get("/api/envios/")

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 0, "el listado no puede filtrar los envíos ajenos"


# ---------------------------------------------------------------- pagos
# Además de la fuga, permitía marcar como pagada la orden de otra persona.


@pytest.mark.django_db
def test_el_listado_de_pagos_solo_muestra_los_propios(otro_client, pago_ajeno):
    respuesta = otro_client.get("/api/pagos/")

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 0


@pytest.mark.django_db
def test_no_se_puede_registrar_un_pago_a_nombre_de_otro(otro_client, usuario, orden_ajena):
    """`usuario` iba en el cuerpo y el serializer lo aceptaba tal cual."""
    respuesta = otro_client.post(
        "/api/pagos/",
        {
            "usuario": usuario.id,
            "orden": orden_ajena.id,
            "monto": "15000.00",
            "metodo": "webpay",
            "estado": "pagado",
        },
        format="json",
    )

    assert respuesta.status_code in (400, 403, 404)
    assert not Pago.objects.filter(usuario=usuario, estado="pagado").exists()


@pytest.mark.django_db
def test_el_estado_del_pago_no_se_puede_fijar_desde_la_peticion(auth_client, usuario, orden_ajena):
    """Un cliente no declara que ya pagó: eso lo dice la pasarela."""
    respuesta = auth_client.post(
        "/api/pagos/",
        {"orden": orden_ajena.id, "monto": "15000.00", "metodo": "webpay", "estado": "pagado"},
        format="json",
    )

    assert respuesta.status_code == 201
    assert Pago.objects.get(pk=respuesta.data["id"]).estado == "pendiente"


# ---------------------------------------------------------------- productos
# El catálogo es de la tienda, no de quien se registre.


@pytest.mark.django_db
def test_cualquiera_puede_ver_el_catalogo(api_client, producto):
    respuesta = api_client.get("/api/productos/productos/")

    assert respuesta.status_code == 200


@pytest.mark.django_db
def test_un_cliente_no_puede_crear_productos(auth_client):
    respuesta = auth_client.post(
        "/api/productos/productos/create/",
        {"nombre": "Gratis", "descripcion": "x", "precio": "1.00", "stock": 99},
        format="json",
    )

    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_un_cliente_no_puede_cambiar_el_precio_de_un_producto(auth_client, producto):
    respuesta = auth_client.patch(
        f"/api/productos/productos/{producto.id}/partial-update/",
        {"precio": "1.00"},
        format="json",
    )

    assert respuesta.status_code == 403
    producto.refresh_from_db()
    assert producto.precio == Decimal("3000.00")


@pytest.mark.django_db
def test_un_cliente_no_puede_borrar_un_producto(auth_client, producto):
    respuesta = auth_client.delete(f"/api/productos/productos/{producto.id}/delete/")

    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_la_duena_de_la_tienda_si_administra_el_catalogo(admin_client_api, producto):
    respuesta = admin_client_api.patch(
        f"/api/productos/productos/{producto.id}/partial-update/",
        {"precio": "4500.00"},
        format="json",
    )

    assert respuesta.status_code == 200
    producto.refresh_from_db()
    assert producto.precio == Decimal("4500.00")


# ---------------------------------------------------------------- reseñas


@pytest.mark.django_db
def test_no_se_puede_publicar_una_resena_suplantando_a_otro(otro_client, usuario, producto):
    respuesta = otro_client.post(
        "/api/reviews/",
        {
            "producto": producto.id,
            "usuario": usuario.id,
            "comentario": "Pésimo, no lo compren",
            "calificacion": 1,
        },
        format="json",
    )

    assert respuesta.status_code == 201
    # La reseña se crea, pero a nombre de quien la escribió, no de la víctima.
    assert not Review.objects.filter(usuario=usuario).exists()
    assert Review.objects.filter(comentario="Pésimo, no lo compren").count() == 1


@pytest.mark.django_db
def test_un_intruso_no_puede_borrar_la_resena_de_otro(otro_client, usuario, producto):
    review = Review.objects.create(
        producto=producto, usuario=usuario, comentario="Excelente", calificacion=5
    )

    respuesta = otro_client.delete(f"/api/reviews/{review.id}/")

    assert respuesta.status_code == 403
    assert Review.objects.filter(pk=review.pk).exists()


# ---------------------------------------------------------------- descuentos


@pytest.mark.django_db
def test_un_cliente_no_puede_crearse_cupones(auth_client):
    respuesta = auth_client.post(
        "/api/descuentos/",
        {
            "nombre": "AUTOREGALO",
            "tipo": "porcentaje",
            "valor": "99.00",
            "fecha_inicio": "2026-01-01",
            "fecha_fin": "2026-12-31",
        },
        format="json",
    )

    assert respuesta.status_code == 403
    assert not Descuento.objects.filter(nombre="AUTOREGALO").exists()


@pytest.mark.django_db
def test_la_duena_de_la_tienda_si_puede_crear_cupones(admin_client_api):
    respuesta = admin_client_api.post(
        "/api/descuentos/",
        {
            "nombre": "VERANO",
            "tipo": "porcentaje",
            "valor": "10.00",
            "fecha_inicio": "2026-01-01",
            "fecha_fin": "2026-12-31",
        },
        format="json",
    )

    assert respuesta.status_code == 201


# ---------------------------------------------------------------- analytics
# El permiso estaba invertido: `IsAuthenticatedOrReadOnly` dejaba LEER a
# cualquiera sin cuenta y exigía sesión solo para escribir.


@pytest.mark.django_db
def test_un_anonimo_no_puede_listar_los_eventos_de_analitica(api_client):
    respuesta = api_client.get("/api/analytics/")

    assert respuesta.status_code in (401, 403)


@pytest.mark.django_db
def test_un_cliente_no_puede_leer_la_analitica_de_la_tienda(auth_client):
    respuesta = auth_client.get("/api/analytics/")

    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_la_duena_de_la_tienda_si_lee_la_analitica(admin_client_api):
    respuesta = admin_client_api.get("/api/analytics/")

    assert respuesta.status_code == 200


# ---------------------------------------------------------------- notificaciones


@pytest.mark.django_db
def test_un_intruso_no_ve_las_notificaciones_de_otro(otro_client, usuario):
    Notificacion.objects.create(
        usuario=usuario, tipo="email", asunto="Tu orden #1", mensaje="Va en camino"
    )

    respuesta = otro_client.get("/api/notificaciones/")

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 0


# ---------------------------------------------------------------- órdenes


@pytest.mark.django_db
def test_un_intruso_no_puede_ver_la_orden_de_otro(otro_client, orden_ajena):
    respuesta = otro_client.get(f"/api/orden/ordenes/{orden_ajena.id}/")

    assert respuesta.status_code == 404


@pytest.mark.django_db
def test_los_endpoints_privados_rechazan_al_anonimo(api_client):
    """Sin token no se entra a ninguna parte del área privada."""
    rutas = ["/api/carrito/carrito/", "/api/orden/ordenes/", "/api/envios/", "/api/pagos/"]

    codigos = [api_client.get(ruta).status_code for ruta in rutas]

    assert all(codigo in (401, 403) for codigo in codigos), dict(zip(rutas, codigos, strict=True))


# ---------------------------------------------------------------- registro


@pytest.mark.django_db
def test_el_registro_rechaza_contrasenas_debiles(api_client):
    """Los AUTH_PASSWORD_VALIDATORS no se aplicaban: DRF no los llama solo."""
    respuesta = api_client.post(
        "/api/auth/register/",
        {
            "username": "nuevo",
            "email": "nuevo@ejemplo.com",
            "password": "12345678",
            "password_confirm": "12345678",
        },
        format="json",
    )

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_el_registro_acepta_una_contrasena_fuerte(api_client):
    respuesta = api_client.post(
        "/api/auth/register/",
        {
            "username": "nuevo",
            "email": "nuevo@ejemplo.com",
            "password": "Tiendita-2026-Segura",
            "password_confirm": "Tiendita-2026-Segura",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert "access" in respuesta.data["token"]


@pytest.mark.django_db
def test_descuento_de_prueba_no_interfiere():
    """Guard: crear un Descuento con DateField no debe reventar (regresión auditlog)."""
    Descuento.objects.create(
        nombre="X",
        tipo="fijo",
        valor=Decimal("1000"),
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
    )

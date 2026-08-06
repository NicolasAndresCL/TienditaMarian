"""Tests de envíos."""

import pytest

from apps.envios.models import Envio
from apps.orden.models import Orden


@pytest.fixture
def envio(db, usuario) -> Envio:
    orden = Orden.objects.create(usuario=usuario, total=150)
    return Envio.objects.create(
        usuario=usuario,
        orden=orden,
        direccion='Calle Falsa 123',
        ciudad='Rancagua',
        codigo_postal='1234567',
        estado='pendiente',
    )


@pytest.mark.django_db
def test_crear_envio(envio):
    assert envio.estado == 'pendiente'
    assert str(envio) == f'Envio {envio.id} - pendiente'


@pytest.mark.django_db
def test_el_dueno_ve_su_envio(auth_client, envio):
    respuesta = auth_client.get(f'/api/envios/{envio.id}/')

    assert respuesta.status_code == 200
    assert respuesta.data['estado'] == 'pendiente'


@pytest.mark.django_db
def test_el_dueno_corrige_la_direccion_de_su_envio(auth_client, envio):
    respuesta = auth_client.patch(
        f'/api/envios/{envio.id}/',
        {'direccion': 'Nueva Dirección 456', 'codigo_postal': '7654321'},
        format='json',
    )

    assert respuesta.status_code == 200
    envio.refresh_from_db()
    assert envio.direccion == 'Nueva Dirección 456'


@pytest.mark.django_db
def test_el_cliente_no_declara_que_su_paquete_ya_salio(auth_client, envio):
    """El estado lo gestiona la tienda: un cliente no marca su envío como enviado."""
    respuesta = auth_client.patch(
        f'/api/envios/{envio.id}/', {'estado': 'entregado'}, format='json'
    )

    assert respuesta.status_code == 200  # el campo se ignora, no rompe la petición
    envio.refresh_from_db()
    assert envio.estado == 'pendiente'


@pytest.mark.django_db
def test_la_tienda_si_avanza_el_estado_del_envio(admin_client_api, envio):
    respuesta = admin_client_api.patch(
        f'/api/envios/{envio.id}/',
        {'estado': 'enviado', 'tracking_id': 'CL-99887766'},
        format='json',
    )

    assert respuesta.status_code == 200
    envio.refresh_from_db()
    assert envio.estado == 'enviado'
    assert envio.tracking_id == 'CL-99887766'

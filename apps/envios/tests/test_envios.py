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
def test_el_dueno_actualiza_su_envio(auth_client, envio, usuario):
    respuesta = auth_client.put(
        f'/api/envios/{envio.id}/',
        {
            'usuario': usuario.id,
            'orden': envio.orden_id,
            'direccion': 'Nueva Dirección 456',
            'ciudad': 'Rancagua',
            'codigo_postal': '7654321',
            'estado': 'enviado',
        },
        format='json',
    )

    assert respuesta.status_code == 200
    assert respuesta.data['estado'] == 'enviado'

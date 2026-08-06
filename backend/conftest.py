"""Fixtures compartidas por toda la suite.

Los tests corren con `config.settings.test`, que hereda de `base`: mismos
INSTALLED_APPS, misma autenticación JWT y los mismos permisos que producción.
Si un test pasa aquí, pasa con la configuración que se despliega.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.productos.models import Producto

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    """Cliente HTTP sin autenticar."""
    return APIClient()


@pytest.fixture
def usuario(db):
    return User.objects.create_user(
        username="marian", email="marian@tiendita.cl", password="clave-segura-123"
    )


@pytest.fixture
def otro_usuario(db):
    """Segundo usuario: existe para probar que NO puede ver los datos del primero."""
    return User.objects.create_user(
        username="intruso", email="intruso@ejemplo.com", password="clave-segura-456"
    )


@pytest.fixture
def admin_usuario(db):
    return User.objects.create_superuser(
        username="nico", email="admin@tiendita.cl", password="clave-admin-789"
    )


@pytest.fixture
def auth_client(api_client, usuario) -> APIClient:
    """Cliente autenticado como `usuario`."""
    api_client.force_authenticate(user=usuario)
    return api_client


@pytest.fixture
def otro_client(api_client, otro_usuario) -> APIClient:
    api_client.force_authenticate(user=otro_usuario)
    return api_client


@pytest.fixture
def admin_client_api(api_client, admin_usuario) -> APIClient:
    api_client.force_authenticate(user=admin_usuario)
    return api_client


@pytest.fixture
def producto(db) -> Producto:
    return Producto.objects.create(
        nombre="Carrito Didáctico",
        descripcion="Un carrito didáctico para el desarrollo de los niños.",
        precio=Decimal("3000.00"),
        stock=10,
    )

"""La sesión de punta a punta: cookies httpOnly, CSRF y rotación del refresh.

Estos tests hacen login **de verdad**. El resto de la suite usa
`force_authenticate`, que salta la autenticación entera: por eso el contrato de
`/auth/token/` podía cambiar sin que nada se pusiera rojo. Aquí se ejercita el
camino que recorre el navegador.
"""

import pytest
from django.conf import settings
from rest_framework.test import APIClient

CLAVE = "clave-segura-123"


def _login(client: APIClient, usuario) -> "object":
    return client.post(
        "/api/v1/auth/token/",
        {"username": usuario.username, "password": CLAVE},
        format="json",
    )


# ------------------------------------------------------------------- login


@pytest.mark.django_db
def test_el_login_deja_la_sesion_en_cookies_httponly(api_client, usuario):
    respuesta = _login(api_client, usuario)

    assert respuesta.status_code == 200

    access = respuesta.cookies[settings.JWT_COOKIE_ACCESS]
    refresh = respuesta.cookies[settings.JWT_COOKIE_REFRESH]

    # httponly es lo que impide que un XSS lea el token desde `document.cookie`.
    assert access["httponly"]
    assert refresh["httponly"]
    assert access["samesite"] == settings.JWT_COOKIE_SAMESITE

    # El refresh solo viaja a las rutas de auth, no en cada petición al catálogo.
    assert refresh["path"] == settings.JWT_COOKIE_REFRESH_PATH


@pytest.mark.django_db
def test_el_refresh_no_viaja_en_el_cuerpo_del_login(api_client, usuario):
    """El token de 7 días nunca debe quedar al alcance del JavaScript.

    El `access` sí se devuelve: dura 15 minutos y es lo que usan el Swagger y los
    clientes de API para autenticarse por cabecera.
    """
    respuesta = _login(api_client, usuario)

    assert "refresh" not in respuesta.data
    assert "access" in respuesta.data


@pytest.mark.django_db
def test_el_registro_tambien_deja_la_sesion_iniciada(api_client):
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
    assert settings.JWT_COOKIE_ACCESS in respuesta.cookies
    assert "refresh" not in respuesta.data["token"]


# --------------------------------------------------- la cookie autentica sola


@pytest.mark.django_db
def test_con_la_cookie_basta_para_leer(api_client, usuario, producto):
    """Sin tocar la cabecera Authorization: es lo que hace el navegador."""
    _login(api_client, usuario)

    respuesta = api_client.get("/api/v1/carrito/")

    assert respuesta.status_code == 200


@pytest.mark.django_db
def test_quien_soy_devuelve_el_usuario_de_la_sesion(api_client, usuario):
    _login(api_client, usuario)

    respuesta = api_client.get("/api/v1/auth/me/")

    assert respuesta.status_code == 200
    assert respuesta.data["username"] == usuario.username


@pytest.mark.django_db
def test_quien_soy_sin_sesion_es_401(api_client):
    assert api_client.get("/api/v1/auth/me/").status_code == 401


# ------------------------------------------------- el token CSRF llega siempre
#
# Los tres endpoints por los que una usuaria puede empezar a usar la tienda
# tienen que dejar el token CSRF puesto. Si falta, la primera petición que
# escriba muere con un 403 — que es exactamente lo que pasaba al registrarse:
# el login lo plantaba y el registro no.


@pytest.mark.django_db
@pytest.mark.parametrize("por_donde_entra", ["login", "registro", "me"])
def test_todo_punto_de_entrada_deja_el_token_csrf(api_client, usuario, por_donde_entra):
    if por_donde_entra == "login":
        respuesta = _login(api_client, usuario)
    elif por_donde_entra == "registro":
        respuesta = api_client.post(
            "/api/v1/auth/register/",
            {
                "username": "otra",
                "email": "otra@ejemplo.com",
                "password": "Tiendita-2026-Segura",
                "password_confirm": "Tiendita-2026-Segura",
            },
            format="json",
        )
    else:
        # `/auth/me/` es lo que el frontend consulta al arrancar: quien ya tenía
        # sesión de una visita anterior entra por aquí, sin pasar por el login.
        _login(api_client, usuario)
        respuesta = api_client.get("/api/v1/auth/me/")

    assert settings.CSRF_COOKIE_NAME in respuesta.cookies


@pytest.mark.django_db
def test_registrarse_y_comprar_sin_pasar_por_el_login(usuario, producto):
    """El recorrido de una clienta nueva, de principio a fin.

    Se registra y agrega algo al carrito. Sin el token CSRF en la respuesta del
    registro, este segundo paso devolvía 403 y la tienda quedaba inutilizable
    justo para quien acababa de crearse la cuenta.
    """
    cliente = APIClient(enforce_csrf_checks=True)

    cliente.post(
        "/api/v1/auth/register/",
        {
            "username": "recien_llegada",
            "email": "recien@ejemplo.com",
            "password": "Tiendita-2026-Segura",
            "password_confirm": "Tiendita-2026-Segura",
        },
        format="json",
    )

    respuesta = cliente.post(
        "/api/v1/carrito/items/",
        {"producto_id": producto.id},
        format="json",
        HTTP_X_CSRFTOKEN=cliente.cookies[settings.CSRF_COOKIE_NAME].value,
    )

    assert respuesta.status_code == 200


# ----------------------------------------------------------------- CSRF
#
# El precio de que el navegador mande la sesión solo: un sitio ajeno puede
# provocar peticiones con la cookie incluida. Con el token en una cabecera eso no
# pasaba, porque la cabecera hay que ponerla a mano.


@pytest.mark.django_db
def test_escribir_solo_con_la_cookie_y_sin_csrf_se_rechaza(usuario, producto):
    cliente = APIClient(enforce_csrf_checks=True)
    _login(cliente, usuario)

    respuesta = cliente.post(
        "/api/v1/carrito/items/", {"producto_id": producto.id}, format="json"
    )

    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_escribir_con_la_cookie_y_el_token_csrf_funciona(usuario, producto):
    cliente = APIClient(enforce_csrf_checks=True)
    # El login responde con `ensure_csrf_cookie`, así que planta el token que el
    # frontend reenvía en la cabecera X-CSRFToken.
    _login(cliente, usuario)
    token_csrf = cliente.cookies[settings.CSRF_COOKIE_NAME].value

    respuesta = cliente.post(
        "/api/v1/carrito/items/",
        {"producto_id": producto.id},
        format="json",
        HTTP_X_CSRFTOKEN=token_csrf,
    )

    assert respuesta.status_code == 200


@pytest.mark.django_db
def test_la_cabecera_bearer_no_necesita_csrf(usuario, producto):
    """Los clientes de API siguen funcionando igual que antes.

    Quien pone la cabecera `Authorization` a mano ya está demostrando que
    controla la petición: ahí CSRF no aporta nada y solo estorbaría al Swagger.
    """
    cliente = APIClient(enforce_csrf_checks=True)
    access = _login(cliente, usuario).data["access"]

    otro = APIClient(enforce_csrf_checks=True)
    respuesta = otro.post(
        "/api/v1/carrito/items/",
        {"producto_id": producto.id},
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {access}",
    )

    assert respuesta.status_code == 200


# -------------------------------------------------------- refresh y logout


@pytest.mark.django_db
def test_el_refresh_se_lee_de_la_cookie_sin_cuerpo(api_client, usuario):
    """El frontend no puede mandar el refresh: no lo ve. Lo pone el navegador."""
    _login(api_client, usuario)
    refresh_original = api_client.cookies[settings.JWT_COOKIE_REFRESH].value

    respuesta = api_client.post("/api/v1/auth/token/refresh/", {}, format="json")

    assert respuesta.status_code == 200
    assert "access" in respuesta.data
    # Con ROTATE_REFRESH_TOKENS el servidor emite uno nuevo y hay que reescribir
    # la cookie; si no, el siguiente refresh usaría uno ya en la blacklist.
    assert api_client.cookies[settings.JWT_COOKIE_REFRESH].value != refresh_original


@pytest.mark.django_db
def test_el_logout_borra_las_cookies(api_client, usuario):
    _login(api_client, usuario)

    respuesta = api_client.post("/api/v1/auth/logout/", {}, format="json")

    assert respuesta.status_code == 205
    # Un valor vacío es como el navegador entiende "olvidá esta cookie". Sin
    # esto, el access seguiría siendo válido sus 15 minutos aunque el refresh ya
    # estuviera en la blacklist.
    assert respuesta.cookies[settings.JWT_COOKIE_ACCESS].value == ""
    assert respuesta.cookies[settings.JWT_COOKIE_REFRESH].value == ""


@pytest.mark.django_db
def test_tras_el_logout_el_refresh_ya_no_sirve(api_client, usuario):
    """La blacklist sigue funcionando: cerrar sesión invalida de verdad."""
    _login(api_client, usuario)
    refresh = api_client.cookies[settings.JWT_COOKIE_REFRESH].value

    api_client.post("/api/v1/auth/logout/", {}, format="json")

    respuesta = api_client.post(
        "/api/v1/auth/token/refresh/", {"refresh": refresh}, format="json"
    )
    assert respuesta.status_code == 401

"""Autenticación por cookie httpOnly, con la cabecera `Bearer` como alternativa.

Por qué existe
--------------
El frontend guardaba los JWT en `localStorage`, que es accesible desde cualquier
JavaScript de la página: un XSS se llevaba la sesión entera, y con el refresh en
la mano tenía siete días de acceso. La mitigación anterior —access de 15 minutos
y blacklist al salir— reduce la ventana, pero no quita el problema: el navegador
seguía entregando el token a cualquier script.

Con una cookie `HttpOnly` el token deja de estar al alcance del JavaScript. El
navegador la adjunta solo cuando corresponde y ningún script puede leerla, ni
siquiera el nuestro.

Lo que eso trae consigo
-----------------------
Una sesión que el navegador envía **sola** es vulnerable a CSRF: un sitio ajeno
puede provocar peticiones a nuestra API con la cookie incluida. Con tokens en una
cabecera eso no pasaba, porque la cabecera hay que ponerla a mano.

Por eso, cuando la autenticación viene por cookie, aquí se exige el token CSRF —
igual que hace `SessionAuthentication` de DRF. Cuando viene por cabecera
`Authorization` no hace falta: quien la pone ya está demostrando que controla la
petición.
"""

from __future__ import annotations

from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication


class _CsrfEstricto(CsrfViewMiddleware):
    """Convierte el rechazo silencioso de CSRF en una excepción con motivo."""

    def _reject(self, request, reason):
        return reason


class JWTCookieAuthentication(JWTAuthentication):
    """Lee el access token de la cookie; si no está, cae en la cabecera.

    El orden importa: la cabecera `Authorization` tiene prioridad, para que el
    Swagger y cualquier cliente de API sigan funcionando igual que antes aunque
    el navegador tenga una cookie de sesión puesta.
    """

    def authenticate(self, request: Request):
        # 1) Cabecera Bearer — el camino de los clientes de API.
        if self.get_header(request) is not None:
            return super().authenticate(request)

        # 2) Cookie — el camino del navegador.
        token_crudo = request.COOKIES.get(settings.JWT_COOKIE_ACCESS)
        if not token_crudo:
            return None

        token = self.get_validated_token(token_crudo)

        # Solo aquí: la petición llegó autenticada sin que nadie pusiera una
        # cabecera, así que hay que comprobar que la originó nuestra aplicación.
        self._exigir_csrf(request)

        return self.get_user(token), token

    def _exigir_csrf(self, request: Request) -> None:
        verificador = _CsrfEstricto(lambda peticion: None)
        motivo = verificador.process_view(request, None, (), {})

        if motivo is not None:
            raise exceptions.PermissionDenied(f"Fallo de verificación CSRF: {motivo}")


class EsquemaDeAutenticacion(OpenApiAuthenticationExtension):
    """Enseña al esquema OpenAPI cómo se autentica esta API.

    drf-spectacular sabe describir las clases de autenticación que conoce, y al
    reemplazar `JWTAuthentication` por la nuestra dejó de saberlo: el esquema
    salía con `securitySchemes` VACÍO y el botón «Authorize» del Swagger dejaba
    de servir para nada. Aquí se declaran las dos vías que acepta
    `JWTCookieAuthentication`.
    """

    target_class = "core.api.authentication.JWTCookieAuthentication"
    name = ["cookieAuth", "bearerAuth"]

    def get_security_definition(self, auto_schema):
        return [
            {
                "type": "apiKey",
                "in": "cookie",
                "name": settings.JWT_COOKIE_ACCESS,
                "description": (
                    "Sesión del navegador. La pone el login y no es accesible "
                    "desde JavaScript; las peticiones que escriben necesitan "
                    "además la cabecera X-CSRFToken."
                ),
            },
            {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": (
                    "Para clientes de API. El `access` viene en el cuerpo del "
                    "login. Por esta vía no se pide CSRF."
                ),
            },
        ]

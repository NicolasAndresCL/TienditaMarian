"""Autenticación: login, refresh, registro y logout."""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.auth_api.cookies import poner_sesion, quitar_sesion
from apps.auth_api.serializers import CustomTokenObtainPairSerializer, RegisterSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


@extend_schema_view(
    post=extend_schema(
        operation_id="auth.login",
        tags=["Autenticación"],
        summary="Iniciar sesión (login JWT)",
        description="Autentica al usuario y devuelve access + refresh token.",
        request=CustomTokenObtainPairSerializer,
        responses={
            200: OpenApiResponse(description="Autenticación exitosa."),
            401: OpenApiResponse(description="Credenciales inválidas."),
            429: OpenApiResponse(description="Demasiados intentos."),
        },
        examples=[
            OpenApiExample(
                name="Credenciales",
                value={"username": "usuario_demo", "password": "clave_segura"},
                request_only=True,
            )
        ],
    )
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    # El login es el endpoint que se ataca por fuerza bruta, y no tenía ningún
    # límite: se podían probar contraseñas sin freno. Su propio scope (10/min)
    # lo separa del resto de la API.
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    # `ensure_csrf_cookie`: la respuesta del login planta el token CSRF que el
    # frontend necesita para las peticiones que escriben. Sin esto, la primera
    # compra tras iniciar sesión fallaría con un 403 de CSRF.
    @method_decorator(ensure_csrf_cookie)
    def post(self, request: Request, *args, **kwargs) -> Response:
        respuesta = super().post(request, *args, **kwargs)

        if respuesta.status_code == status.HTTP_200_OK:
            refresh = respuesta.data.pop("refresh")
            # El `access` se conserva en el cuerpo para el Swagger y los clientes
            # de API; el `refresh` —el de siete días, el que de verdad hay que
            # proteger— sale SOLO en una cookie httpOnly y nunca es visible al
            # JavaScript. El frontend no guarda ninguno de los dos.
            poner_sesion(respuesta, access=respuesta.data["access"], refresh=refresh)

        return respuesta


@extend_schema_view(
    post=extend_schema(
        operation_id="auth.refresh",
        tags=["Autenticación"],
        summary="Renovar access token",
        description="Usa un refresh token válido para generar un nuevo token de acceso.",
        responses={
            200: OpenApiResponse(description="Token renovado."),
            401: OpenApiResponse(description="Token inválido o expirado."),
        },
    )
)
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request: Request, *args, **kwargs) -> Response:
        # El refresh llega por cookie (navegador) o en el cuerpo (clientes de
        # API). La cookie no se puede leer desde JavaScript, así que el frontend
        # no tiene forma de mandarlo en el cuerpo aunque quisiera.
        if not request.data.get("refresh"):
            desde_cookie = request.COOKIES.get(settings.JWT_COOKIE_REFRESH)
            if desde_cookie:
                request.data["refresh"] = desde_cookie

        respuesta = super().post(request, *args, **kwargs)

        if respuesta.status_code == status.HTTP_200_OK:
            # Con ROTATE_REFRESH_TOKENS el servidor emite uno nuevo: hay que
            # reescribir la cookie o el siguiente refresh usaría el ya
            # invalidado por la blacklist.
            nuevo_refresh = respuesta.data.pop("refresh", None)
            poner_sesion(respuesta, access=respuesta.data["access"], refresh=nuevo_refresh)

        return respuesta


@extend_schema_view(
    post=extend_schema(
        operation_id="auth.register",
        tags=["Usuarios"],
        summary="Registro de nuevo usuario",
        description="Registra un usuario y emite sus tokens JWT.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description="Usuario creado y autenticado."),
            400: OpenApiResponse(description="Datos inválidos o contraseña débil."),
        },
        examples=[
            OpenApiExample(
                name="Registro",
                # El ejemplo anterior sugería "123456", una contraseña que hoy el
                # validador rechaza. Un ejemplo del Swagger es documentación: no
                # puede enseñar a usar claves débiles.
                value={
                    "username": "marian",
                    "email": "marian@ejemplo.com",
                    "password": "Tiendita-2026-Segura",
                    "password_confirm": "Tiendita-2026-Segura",
                },
                request_only=True,
            )
        ],
    )
)
class RegisterAPIView(mixins.CreateModelMixin, GenericAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    # Igual que el login: el registro deja la sesión iniciada, así que tiene que
    # dejar también el token CSRF o la primera compra moriría con un 403.
    @method_decorator(ensure_csrf_cookie)
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()

        # Antes se hacía `User.objects.get(username=response.data["username"])`
        # para recuperar el usuario recién creado: una consulta de más y una
        # carrera si dos registros compiten. `serializer.save()` ya lo devuelve.
        refresh = RefreshToken.for_user(usuario)
        logger.info("Usuario registrado: %s", usuario.username)

        respuesta = Response(
            {
                "message": "Usuario creado exitosamente.",
                "usuario": {"username": usuario.username, "email": usuario.email},
                # Igual que en el login: el access sigue en el cuerpo para los
                # clientes de API, el refresh solo en la cookie httpOnly.
                "token": {"access": str(refresh.access_token)},
            },
            status=status.HTTP_201_CREATED,
        )

        return poner_sesion(respuesta, access=str(refresh.access_token), refresh=str(refresh))


@extend_schema_view(
    get=extend_schema(
        operation_id="auth.me",
        tags=["Autenticación"],
        summary="Quién soy",
        description=(
            "Datos del usuario de la sesión actual. Con la sesión en una cookie "
            "httpOnly, el frontend no puede inspeccionar el token para saber si "
            "hay sesión ni de quién es: lo pregunta aquí al arrancar."
        ),
        responses={
            200: OpenApiResponse(description="Sesión activa."),
            401: OpenApiResponse(description="Sin sesión."),
        },
    )
)
class MeAPIView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None

    # El frontend llama aquí al arrancar, así que es el sitio natural para
    # plantar el token CSRF: garantiza que esté disponible antes de la primera
    # petición que escriba, venga la usuaria de donde venga.
    @method_decorator(ensure_csrf_cookie)
    def get(self, request: Request) -> Response:
        return Response(
            {
                "username": request.user.username,
                "email": request.user.email,
                "es_staff": request.user.is_staff,
            }
        )


@extend_schema_view(
    post=extend_schema(
        operation_id="auth.logout",
        tags=["Autenticación"],
        summary="Cerrar sesión",
        description=(
            "Invalida el refresh token enviándolo a la blacklist. Sin esto, un "
            "token robado seguía siendo válido durante los 7 días de su vigencia "
            "aunque el usuario hubiera cerrado sesión."
        ),
        request={"application/json": {"type": "object", "properties": {"refresh": {"type": "string"}}}},
        responses={
            205: OpenApiResponse(description="Sesión cerrada."),
            400: OpenApiResponse(description="Token ausente o inválido."),
        },
    )
)
class LogoutAPIView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None

    def post(self, request: Request) -> Response:
        token_refresh = request.data.get("refresh") or request.COOKIES.get(
            settings.JWT_COOKIE_REFRESH
        )

        if not token_refresh:
            return Response(
                {"error": {"codigo": "refresh_requerido", "mensaje": "Falta el refresh token.", "detalle": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            RefreshToken(token_refresh).blacklist()
        except TokenError:
            # Token ya vencido o ya invalidado: la sesión del navegador se cierra
            # igual —las cookies se borran abajo—, pero se avisa que venía mal.
            return quitar_sesion(
                Response(
                    {"error": {"codigo": "token_invalido", "mensaje": "El token no es válido.", "detalle": {}}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            )

        logger.info("Sesión cerrada: %s", request.user.username)
        # Sin borrar las cookies, el navegador seguiría mandando un access válido
        # durante sus 15 minutos de vida aunque el refresh ya esté en la blacklist.
        return quitar_sesion(Response(status=status.HTTP_205_RESET_CONTENT))

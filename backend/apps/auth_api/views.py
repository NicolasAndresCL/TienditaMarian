"""Autenticación: login, refresh, registro y logout."""

import logging

from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()

        # Antes se hacía `User.objects.get(username=response.data["username"])`
        # para recuperar el usuario recién creado: una consulta de más y una
        # carrera si dos registros compiten. `serializer.save()` ya lo devuelve.
        refresh = RefreshToken.for_user(usuario)
        logger.info("Usuario registrado: %s", usuario.username)

        return Response(
            {
                "message": "Usuario creado exitosamente.",
                "usuario": {"username": usuario.username, "email": usuario.email},
                "token": {"access": str(refresh.access_token), "refresh": str(refresh)},
            },
            status=status.HTTP_201_CREATED,
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
        token_refresh = request.data.get("refresh")
        if not token_refresh:
            return Response(
                {"error": {"codigo": "refresh_requerido", "mensaje": "Falta el refresh token.", "detalle": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            RefreshToken(token_refresh).blacklist()
        except TokenError:
            # Token ya vencido o ya invalidado: el resultado buscado (sesión
            # cerrada) igualmente se cumple, pero se avisa que venía mal.
            return Response(
                {"error": {"codigo": "token_invalido", "mensaje": "El token no es válido.", "detalle": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info("Sesión cerrada: %s", request.user.username)
        return Response(status=status.HTTP_205_RESET_CONTENT)

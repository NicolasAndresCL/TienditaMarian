from django.contrib.auth.models import User
from rest_framework import mixins, permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from auth_api.serializers import CustomTokenObtainPairSerializer, RegisterSerializer
from drf_spectacular.utils import (
    extend_schema_view, extend_schema,
    OpenApiExample, OpenApiResponse
)

@extend_schema_view(
    post=extend_schema(
        operation_id="auth.login",
        tags=["Autenticación"],
        summary="Iniciar sesión (login JWT)",
        description="Autentica al usuario y devuelve access + refresh token.",
        request=CustomTokenObtainPairSerializer,
        responses={
            200: OpenApiResponse(response={"access": "jwt-token", "refresh": "refresh-token"}, description="Autenticación exitosa."),
            401: OpenApiResponse(description="Credenciales inválidas")
        },
        examples=[
            OpenApiExample(
                name="Credenciales",
                value={"username": "usuario_demo", "password": "clave_segura"},
                request_only=True
            )
        ]
    )
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema_view(
    post=extend_schema(
        operation_id="auth.refresh",
        tags=["Autenticación"],
        summary="Renovar access token",
        description="Usa un refresh token válido para generar un nuevo token de acceso.",
        responses={
            200: OpenApiResponse(response={"access": "nuevo-access-token"}, description="Token renovado."),
            401: OpenApiResponse(description="Token inválido o expirado")
        },
        examples=[
            OpenApiExample(
                name="Refresh válido",
                value={"refresh": "jwt-refresh-token"},
                request_only=True
            )
        ]
    )
)
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


@extend_schema_view(
    post=extend_schema(
        operation_id="auth.register",
        tags=["Usuarios"],
        summary="Registro de nuevo usuario",
        description="Registra un usuario y emite tokens JWT automáticamente.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description="Usuario creado y autenticado."),
            400: OpenApiResponse(description="Datos inválidos.")
        },
        examples=[
            OpenApiExample(
                name="Registro básico",
                value={"username": "nicolás_dev", "email": "nico@ejemplo.com", "password": "123456"},
                request_only=True
            )
        ]
    )
)
class RegisterAPIView(mixins.CreateModelMixin, GenericAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = self.create(request, *args, **kwargs)
        user = User.objects.get(username=response.data["username"])
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Usuario creado exitosamente.",
            "usuario": response.data,
            "token": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        }, status=status.HTTP_201_CREATED)

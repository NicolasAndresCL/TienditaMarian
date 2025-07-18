from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import generics
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from auth_api.serializers import CustomTokenObtainPairSerializer, RegisterSerializer
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

@extend_schema(
    tags=["Autenticación"],
    description="Genera un nuevo token JWT para el usuario autenticado."
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=["Autenticación"],
    description="Refresca el token JWT usando el refresh token."
)
class CustomTokenRefreshView(TokenRefreshView):
    pass

@extend_schema(tags=["Usuarios"])
class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(username=response.data['username'])
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Usuario creado exitosamente",
            "usuario": response.data,
            "token": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        })
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token


class RegisterSerializer(serializers.ModelSerializer):
    """Registro de una clienta nueva.

    Antes la única exigencia era `min_length=8`: "12345678" pasaba sin problema.
    Los AUTH_PASSWORD_VALIDATORS configurados en el settings **no se aplicaban**,
    porque DRF no los llama por su cuenta — hay que invocarlos explícitamente.
    """

    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        return value

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            # Los validadores de Django hablan su propio dialecto de excepciones;
            # hay que traducirlas para que DRF las devuelva como un 400 y no como
            # un 500.
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, data: dict) -> dict:
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})
        return data

    def create(self, validated_data: dict) -> User:
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)

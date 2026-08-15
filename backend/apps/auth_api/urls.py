from django.urls import path

from apps.auth_api.views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutAPIView,
    MeAPIView,
    RegisterAPIView,
)

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterAPIView.as_view(), name='user-register'),
    path('logout/', LogoutAPIView.as_view(), name='user-logout'),
    # El frontend no puede leer la cookie httpOnly, así que pregunta aquí si hay
    # sesión y de quién es.
    path('me/', MeAPIView.as_view(), name='user-me'),
]

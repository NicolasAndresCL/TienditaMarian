from django.urls import path
from apps.auth_api.views import CustomTokenObtainPairView, RegisterAPIView, CustomTokenRefreshView

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterAPIView.as_view(), name='user-register'),
]

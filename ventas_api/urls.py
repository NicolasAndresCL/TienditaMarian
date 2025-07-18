from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from productos.views.home_view import home
# ViewSets
from productos.views.producto_views import ProductoViewSet

# JWT y documentación
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Router para productos
productos_router = DefaultRouter()
productos_router.register(r'', ProductoViewSet, basename='producto')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home
    path('', home, name='home'),

    # Productos
    path('api/productos/', include(productos_router.urls)),

    # Carrito
    path('api/carrito/', include('carrito.urls')),

    # Órdenes
    path('api/ordenes/', include('orden.urls')),

    # Autenticación
    path('api/auth/', include('auth_api.urls')),


    # Documentación
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Archivos estáticos en modo debug
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

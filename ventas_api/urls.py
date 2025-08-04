from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from productos.views.home_view import home

from drf_spectacular.views import (
    SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
)

urlpatterns = [
    # 🛠️ Administración
    path('admin/', admin.site.urls),

    # 🏠 Vista principal
    path('', home, name='home'),

    # 📦 Módulos API agrupados
    path('api/productos/', include('productos.urls')),
    path('api/carrito/', include('carrito.urls')),
    path('api/ordenes/', include('orden.urls')),
    path('api/auth/', include('auth_api.urls')),

    # 📘 Documentación Swagger/OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# 🖼️ Archivos estáticos solo en DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

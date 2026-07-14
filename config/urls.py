from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

from apps.productos.views.home_view import home


def custom_swagger_ui_view(request):
    return render(request, "swagger/custom_swagger.html")

urlpatterns = [
    # 🛠️ Administración
    path('admin/', admin.site.urls),

    # 🏠 Vista principal
    path('', home, name='home'),

    # 📦 Módulos API agrupados
    path('api/productos/', include('apps.productos.urls')),
    path('api/carrito/', include('apps.carrito.urls')),
    path('api/orden/', include('apps.orden.urls')),
    path('api/pagos/', include('apps.pagos.urls')),
    path('api/envios/', include('apps.envios.urls')),
    path('api/notificaciones/', include('apps.notificaciones.urls')),
    path('api/descuentos/', include('apps.descuentos.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/auth/', include('apps.auth_api.urls')),

    # 📘 Documentación Swagger/OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', custom_swagger_ui_view, name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# 🖼️ Archivos estáticos solo en DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

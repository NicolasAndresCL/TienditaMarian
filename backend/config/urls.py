"""Rutas raíz del proyecto.

La API vive bajo `/api/v1/` (ver `config/api_urls.py`). Las rutas anteriores se
mantienen en paralelo mientras se migra el frontend —strangler-fig, skill §3: la
versión vieja sigue operativa hasta alcanzar paridad— y se eliminarán en cuanto
`Frontend-Tiendita` apunte a v1.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

from apps.productos.views.home_view import home
from core.views import healthz


def custom_swagger_ui_view(request):
    return render(request, "swagger/custom_swagger.html")


urlpatterns = [
    path('admin/', admin.site.urls),

    # Vitrina HTML. No es parte de la API (antes colgaba de /api/productos/).
    path('', home, name='home'),

    # Salud del servicio: la consultan Docker, el orquestador y los monitores.
    path('healthz/', healthz, name='healthz'),

    # API v1 — rutas limpias y versionadas.
    path('api/v1/', include('config.api_urls')),

    # ------------------------------------------------------------------
    # DEPRECADAS — rutas de la v0. Repetían el nombre de la app dentro de su
    # propio prefijo (/api/productos/productos/, /api/carrito/carrito/add/).
    # Siguen vivas solo para no romper el frontend actual; se borran al migrarlo.
    # ------------------------------------------------------------------
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

    # Documentación OpenAPI.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', custom_swagger_ui_view, name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

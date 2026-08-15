"""Rutas raíz del proyecto.

Toda la API vive bajo `/api/v1/` (ver `config/api_urls.py`).

Las rutas de la v0 —que repetían el nombre de la app dentro de su propio prefijo
(`/api/productos/productos/`, `/api/carrito/carrito/add/`)— se mantuvieron en
paralelo mientras el frontend migraba (strangler-fig, skill §3) y **ya se
eliminaron**: `frontend/src/api/client.js` apunta a `/api/v1` desde su baseURL, y
no queda ningún consumidor de las viejas.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path, re_path
from django.views.static import serve
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

    # Documentación OpenAPI.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', custom_swagger_ui_view, name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
elif settings.SERVE_MEDIA:
    # `static()` devuelve una lista vacía cuando DEBUG=False, y WhiteNoise sirve
    # los estáticos pero no el media subido: por eso las fotos del catálogo daban
    # 404 en la imagen de producción. Aquí se publica la ruta a propósito, para
    # el compose local y las demos.
    # En un despliegue real esto va en False y el media lo sirve nginx o un CDN:
    # `serve` es síncrono y no está pensado para tráfico serio.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

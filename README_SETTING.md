# 📘 README_setting – Tiendita de Marian Backend
## 🛒 Proyecto Django + DRF + JWT + MySQL
API robusta y modular para administrar productos en una tienda virtual. Incluye autenticación JWT, documentación OpenAPI decorada con drf-spectacular, y conexión al frontend Vite + React.

## ⚙️ Estructura base del proyecto
```bash
TienditaMarian/
├── config/             # Configuración global del proyecto Django
│   ├── settings.py     # Parámetros de entorno, apps, base de datos, JWT, CORS, etc.
│   ├── urls.py         # Rutas principales y documentación Swagger
│   ├── wsgi.py         # Entrada WSGI para despliegue
│   └── asgi.py         # Entrada ASGI para WebSockets (opcional)
├── apps/               # Apps modulares del backend
│   ├── productos/      # Catálogo de productos
│   ├── carrito/        # Lógica de carrito y checkout
│   ├── orden/          # Gestión de órdenes
│   ├── auth_api/       # Autenticación JWT
│   ├── pagos/          # Integración con pasarelas
│   ├── envios/         # Cálculo y seguimiento de envíos
│   ├── notificaciones/ # Correos y alertas
│   ├── descuentos/     # Cupones y promociones
│   └── reviews/        # Reseñas y ratings
├── media/              # Imágenes subidas por usuarios
├── staticfiles/        # Archivos estáticos recolectados
├── manage.py
```
## 🧪 Configuración avanzada (config/settings.py)
Sección	          |Descripción
------------------|------------------
BASE_DIR	        |Ruta raíz del proyecto
SECRET_KEY	      |Cargada desde .env con python-decouple
DEBUG	            |Activado para desarrollo
ALLOWED_HOSTS	    |Configurado según entorno (.env.dev, .env.main)
INSTALLED_APPS	  |Django, DRF, JWT, CORS, y todas las apps bajo apps/
DATABASES	        |Conexión a MySQL, credenciales desde .env
STATICFILES_DIRS	|Archivos estáticos de apps
MEDIA_ROOT / URL	|Carpeta media/ para imágenes subidas
REST_FRAMEWORK	  |API protegida con JWT, paginación y documentación
SIMPLE_JWT	      |Tokens configurados para login, duración y headers
CORS_ALLOWED_ORIGINS |	Permite conexión desde http://localhost:5173 (frontend Vite)

## 🧩 Selección automática de entorno

.env.dev para desarrollo local

.env.main para producción

Git hook post-checkout selecciona el entorno según la rama

Variable ENV_FILE determina qué archivo se carga dinámicamente

## 🔐 Autenticación JWT
```bash
POST /api/token/
{
  "username": "admin",
  "password": "tu_contraseña"
}
Usar el token en el header:

http
Authorization: Bearer <access_token>
```

## 🖼️ Servir imágenes en desarrollo
Modelo Producto usa ImageField(upload_to='productos/')

Las imágenes se guardan en media/productos/

Acceso desde React:

jsx
<img src={`http://localhost:8000${producto.imagen}`} />
## 📦 Endpoints organizados por módulo
```python
# config/urls.py
urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/productos/', include('apps.productos.urls')),
    path('api/carrito/', include('apps.carrito.urls')),
    path('api/orden/', include('apps.orden.urls')),
    path('api/auth/', include('apps.auth_api.urls')),
    ...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```
## 🎨 Decoración profesional de Swagger UI
Cada vista DRF incluye:

Propiedad          |	Descripción
-------------------|----------------------------------
operation_id	     |Nombre semántico del endpoint (listar_productos, checkout_orden, etc.)
summary            |	Descripción breve visible en Swagger
description	       |Explicación detallada por endpoint
tags	             |Agrupación visual por módulo (Productos, Órdenes, etc.)
examples	         |Ejemplos de request/response
responses	         |Definición clara por código HTTP (200, 201, 404, etc.)

## ⚙️ SPECTACULAR_SETTINGS personalizado

Propiedad           |	Valor / Descripción
--------------------|------------------------------
TITLE	              |Tiendita de Marian API 📦
DESCRIPTION	        |Documentación visual para onboarding y entrevistas técnicas
CONTACT / LICENSE	  |Branding personal + licencia MIT
SECURITY	JWT       |documentado en Swagger
displayOperationId	|Activado para mostrar nombres semánticos
SWAGGER_UI_SETTINGS	|UX mejorada: duración de peticiones, autorización persistente

## 🔧 Refactor técnico
✅ Vistas migradas a GenericAPIView + mixins
Separación clara por acción (ListModelMixin, CreateModelMixin, etc.)

Modularidad por endpoint

Facilidad para testing y documentación por clase

🔄 Paginación en listados
Implementada con PageNumberPagination

Mejora la navegación en Swagger UI y frontend

## ✨ Resultado final
La API está lista para:

Integrarse con frontend multiplataforma

Ser navegada visualmente por reclutadores o colaboradores

Exportar su schema OpenAPI como documentación formal

Escalar fácilmente con permisos, filtros, roles y nuevos módulos

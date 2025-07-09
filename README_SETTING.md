# 📘 README – Tiendita de Marian Backend

## 🛒 Proyecto Django + DRF + JWT + MySQL

API desarrollada para administrar productos en una tienda virtual, con autenticación JWT, documentación OpenAPI con drf-spectacular, y conexión al frontend Vite + React.
---
## ⚙️ Estructura base del proyecto
```TienditaMarian/
├── ventas_api/         # Proyecto principal de Django
│   └── settings.py     # Configuración global del proyecto
├── productos/          # App que gestiona productos
│   └── models.py       # Modelo de producto
│   └── serializers.py  # Serializador de producto
│   └── views.py        # Vistas DRF
│   └── urls.py         # Endpoints de producto
├── media/              # Carpeta dinámica para imágenes subidas
├── staticfiles/        # Archivos estáticos recolectados
├── db.sqlite3 / MySQL  # Base de datos (usa MySQL configurado)
├── manage.py
```
---
## 🧪 settings.py - Configuración explicada

| Sección             | Descripción                                                                 |
|---------------------|------------------------------------------------------------------------------|
| `BASE_DIR`          | Ruta raíz del proyecto                                                      |
| `SECRET_KEY`        | Clave secreta cargada desde `.env` con `python-decouple`                   |
| `DEBUG`             | Activo para desarrollo                                                      |
| `ALLOWED_HOSTS`     | Permitir dominiios (vacío en local)                                         |
| `INSTALLED_APPS`    | Incluye Django básico, DRF, CORS, JWT y tu app `productos`                 |
| `MIDDLEWARE`        | Incluye `corsheaders` para conexión segura con frontend Vite               |
| `DATABASES`         | Configurado con MySQL (nombre, usuario, contraseña desde `.env`)           |
| `STATICFILES_DIRS`  | Archivos estáticos de la app `productos`                                   |
| `MEDIA_ROOT / URL`  | Carpeta `media/` para servir imágenes subidas desde admin                  |
| `REST_FRAMEWORK`    | API protegida con JWT y documentación vía `drf-spectacular`                |
| `SIMPLE_JWT`        | Configura tokens para login, duración y headers                            |
| `CORS_ALLOWED_ORIGINS`| Permite conexión desde `http://localhost:5173` (tu frontend Vite)        |
---
## 📦 Endpoints de la API
En tu productos/urls.py y ventas_api/urls.py, registrá los routers de DRF, junto con rutas extra para login y Swagger.

Ejemplo:

```python
# ventas_api/urls.py
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/', include('productos.urls')),
]

# Sirve archivos media en desarrollo
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```
---
## 🔐 Autenticación
Usás JWT para proteger los endpoints. Podés obtener el token desde una ruta tipo:

```bash
POST /api/token/
{
  "username": "admin",
  "password": "tu_contraseña"
}
```

El token se usa con el header:

```Authorization: Bearer <access_token>
```
---
## 🖼️ Servir imágenes subidas en desarrollo

- Asegurate que el modelo Producto use ImageField con upload_to='productos/'

- Los archivos se guardarán en media/productos/

- Acceden desde React vía:

```jsx
<img src={`http://localhost:8000${producto.imagen}`} />
```
---
## 🧪 Swagger + documentación

- http://localhost:8000/api/schema/ → Schema OpenAPI

- http://localhost:8000/api/docs/ → Swagger interactivo

---

## 🧩 .env ejemplo
```SECRET_KEY=tu_clave_secreta
DATABASES_USER=tu_usuario_mysql
DATABASES_PASSWORD=tu_password_mysql
```

## ✅ Pendientes sugeridos

- Agregar paginación y filtros en views.py

- Habilitar subida de imágenes desde el frontend

- Implementar permisos por rol

- Agregar tests unitarios y de integración
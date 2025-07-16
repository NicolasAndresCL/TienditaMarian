
# 🛍️ Tiendita de Marian

**Tiendita de Marian** es una tienda en línea creada con Django y Django REST Framework. Ofrece una API robusta, segura y desacoplada para la gestión de productos y compras, incluyendo autenticación JWT, carrito de compras, checkout, historial de órdenes, webhooks de email, paginación, filtros avanzados, pruebas automáticas y documentación OpenAPI lista para producción.

---


## 📦 Tech Stack

- **Backend**: Django 5 + Django REST Framework
- **Autenticación**: JWT (`djangorestframework-simplejwt`)
- **Carrito y Checkout**: Lógica desacoplada, endpoints RESTful
- **Documentación**: OpenAPI/Swagger (`drf-spectacular`)
- **Webhooks**: Notificación por email al crear órdenes
- **Seguridad**: Variables protegidas con `.env` (`python-decouple`)
- **Pruebas**: Unitarias con Django TestCase
- **Versionado**: Git
- **Base de datos**: SQLite (desarrollo) / MySQL (producción-ready)

---

## ⚙️ Instalación

```bash
git clone https://github.com/tuusuario/tiendita-marian.git
cd tiendita-marian
python -m venv env
source env/bin/activate  # en Windows: env\Scripts\activate
pip install -r requirements.txt
```
---

## Configura el archivo .env con tu SECRET_KEY:

```SECRET_KEY='tu_clave_segura'
```
---

## Aplica migraciones:

```bash
python manage.py makemigrations
python manage.py migrate
```
---

## Ejecuta el servidor:

```bash
python manage.py runserver
```
---

## 🔐 JWT Authentication

Obtención de token:

```POST /api/token/
{
  "username": "tu_usuario",
  "password": "tu_contraseña"
}
```

Refresh token:

```POST /api/token/refresh/
{
  "refresh": "tu_refresh_token"
}
```

Incluye el token en tus peticiones:

```Authorization: Bearer <access_token>
```
---

## 🛠️ Features

- CRUD de productos
- Carrito de compras persistente por usuario (añadir, eliminar, actualizar cantidades)
- Checkout y creación de órdenes
- Historial de órdenes paginado y filtrable por usuario
- Detalle de orden específica
- Endpoints protegidos con JWT (access y refresh tokens)
- Webhook: notificación por email al crear una orden
- Documentación OpenAPI/Swagger autogenerada y sin warnings
- Pruebas automáticas para carrito, checkout y notificaciones
- Backend modular, desacoplado y listo para producción
- Admin interface habilitada para gestión rápida
---
## 🧱 Estructura del proyecto

```tiendita-backend-django/
├── productos/                        # App principal de productos y carrito
│   ├── migrations/
│   ├── templates/
│   │   └── productos/
│   ├── static/
│   │   └── productos/               # Archivos estáticos (si aplica)
│   ├── admin.py                     # Registro de modelos
│   ├── apps.py
│   ├── models.py                    # Modelo Producto
│   ├── serializers.py               # DRF Serializers (Producto)
│   ├── views.py                     # API productos
│   ├── urls.py                      # Rutas productos
│   ├── tests.py
│   ├── carrito_models.py            # Modelos: Carrito, ItemCarrito, Orden, ItemOrden
│   ├── carrito_serializers.py       # Serializers: Carrito, Orden, etc.
│   ├── carrito_views.py             # Endpoints: carrito, checkout, historial, detalle orden
│   ├── carrito_urls.py              # Rutas carrito/orden
│
├── ventas_api/                      # Configuración global del proyecto
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                  # Configuración con .env, JWT, email, CORS
│   ├── urls.py                      # URLs globales
│   └── wsgi.py
│
├── staticfiles/                     # Static files recolectados (¡ignorar en Git!)
├── manage.py
├── .env                             # Variables sensibles (no versionar)
├── requirements.txt                 # Instalaciones necesarias
├── .gitignore                       # Ignora env, .env, staticfiles, etc.
├── checklist.md                     # Guía de pasos realizados
└── README.md                        # Documentación del proyecto
```
---

## 📌 Avances realizados

- [x] Sistema de carrito de compras y checkout 100% funcional
- [x] Endpoints protegidos con JWT (login, refresh, autorización)
- [x] Historial de órdenes paginado y filtrable por usuario
- [x] Endpoint para ver detalle de una orden específica
- [x] Endpoint para actualizar cantidad de un producto en el carrito
- [x] Webhook: notificación por email al crear una orden
- [x] Documentación OpenAPI/Swagger sin warnings (drf-spectacular)
- [x] Pruebas automáticas para carrito, checkout y notificaciones
- [x] Organización de imágenes y archivos estáticos
- [x] Limpieza de warnings/errores en documentación y código

## 🚀 Próximos pasos sugeridos

- [ ] Vista personalizada de login con JWT
- [ ] Roles y permisos avanzados por tipo de usuario
- [ ] Conexión a PostgreSQL o MySQL en producción
- [ ] Despliegue (Render / Railway / Vercel)
- [ ] Integración frontend (React + Vite)

---


## 🧑‍💻 Autor
Nicolás Andrés Cano Leal — Backend Developer especializado en APIs robustas con Django REST Framework y FastAPI.

“Una tienda simple hecha con principios sólidos: escalabilidad, seguridad y código limpio.”


---

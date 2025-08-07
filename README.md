# 🛍️ Tiendita de Marian

**Tiendita de Marian** es una tienda en línea construida con Django y Django REST Framework. Ofrece una API robusta, segura y modular para la gestión de productos, usuarios y compras. Incluye autenticación JWT, carrito de compras persistente, checkout, historial de órdenes, notificaciones por email, documentación OpenAPI sin warnings, y pruebas automáticas por dominio.

---

## 📦 Tech Stack

- **Backend**: Django 5 + Django REST Framework
- **Autenticación**: JWT (`djangorestframework-simplejwt`)
- **Documentación**: OpenAPI/Swagger (`drf-spectacular`)
- **Seguridad**: Variables protegidas con `.env` (`python-decouple`)
- **Pruebas**: Unitarias con `TestCase` por módulo
- **Base de datos**: SQLite (desarrollo) / MySQL o PostgreSQL (producción-ready)
- **Versionado**: Git
- **Despliegue sugerido**: Render / Railway / Vercel

---

## ⚙️ Instalación

```bash
git clone https://github.com/tuusuario/tiendita-marian.git
cd tiendita-marian
python -m venv env
source env/bin/activate  # en Windows: env\Scripts\activate
pip install -r requirements.txt
```
## 🔐 Configuración
Crea un archivo `.env` en la raíz del proyecto:`

```
SECRET_KEY='tu_clave_segura'
DEBUG=True
EMAIL_HOST_USER='tu_correo@gmail.com'
EMAIL_HOST_PASSWORD='tu_contraseña_app'
```
## 🧩 Migraciones y ejecución

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## 🔐 Autenticación JWT + Registro

La API incluye endpoints para login, refresh y registro de usuarios con validaciones y autologin.

__Endpoints__
- POST /api/auth/register/ Registra un nuevo usuario y devuelve el token automáticamente.

- POST /api/auth/token/ Autentica al usuario y devuelve el token JWT.

- POST /api/auth/token/refresh/ Refresca el token usando el refresh token.

__Validaciones__
- Email único
- Contraseñas coincidentes
- Longitud mínima de contraseña

Ejemplo de respuesta al registrar:
```
json
{
  "message": "Usuario creado exitosamente",
  "usuario": {
    "username": "nicolas",
    "email": "nicolas@example.com"
  },
  "token": {
    "access": "eyJ0eXAiOiJKV1QiLCJh...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJh..."
  }
}
```
## 🛠️ Features
- CRUD de productos con paginación y filtros

- Carrito de compras persistente por usuario (añadir, eliminar, actualizar cantidades)

- Checkout y creación de órdenes

- Historial de órdenes paginado y filtrable por usuario

- Detalle de orden específica

- Endpoints protegidos con JWT (access y refresh tokens)

- Webhook: notificación por email al crear una orden

- Documentación OpenAPI/Swagger autogenerada y agrupada por dominio

- Pruebas automáticas por módulo (productos, carrito, orden, auth_api)

- Backend modular, desacoplado y listo para producción

- Admin interface habilitada para gestión rápida

## 🧱 Estructura del proyecto

```
tiendita-backend-django/
│
├── ventas_api/                  # Configuración global del proyecto
│   ├── settings.py              # Configuración con .env, JWT, email, CORS
│   ├── urls.py                  # URLs globales por dominio
│   ├── checklist.md             # Tareas técnicas y próximos pasos
│   ├── README_SETTING.md        # Documentación específica de configuración
│
├── productos/              # CRUD de productos y lógica compartida con carrito
│   ├── views/
│   │   ├── home_view.py
│   │   └── producto_views.py
│   ├── serializers/
│   │   └── producto_serializers.py
│   ├── services/
│   │   └── carrito_service.py
│   ├── tests/
│   │   ├── test_home.py
│   │   └── test_productos.py
│   └── urls.py

├── carrito/                     # Lógica de carrito y checkout
│   ├── views/
│   │   └── carrito_views.py
│   ├── serializers/
│   │   └── carrito_serializers.py
│   ├── tests/
│   │   └── test_carrito.py
│   └── urls/
│       └── carrito_urls.py

├── orden/                       # Gestión de órdenes y señales
│   ├── views.py
│   ├── serializers.py
│   ├── signals.py
│   ├── tests.py
│   └── urls.py

├── auth_api/                    # Autenticación JWT y registro de usuarios
│   ├── views/
│   │   └── auth_views.py
│   ├── serializers/
│   │   └── auth_serializers.py
│   ├── tests/
│   │   └── test_auth.py
│   └── urls/
│       └── auth_urls.py

├── staticfiles/                 # Archivos estáticos recolectados
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## 🧪 Pruebas

```bash
python manage.py test
```
## 📜 Documentación
```bash
python manage.py generate_swagger
```
La documentación de la API está disponible en `/api/docs/` y se genera automáticamente con `drf-spectacular`. Incluye todos los endpoints, parámetros, respuestas y ejemplos.

### 🪝 Git Hooks personalizados

Este proyecto utiliza hooks versionables para automatizar tareas:

- `post-checkout`: selecciona automáticamente el entorno `.env` según la rama (`main` o `dev`)
- Ubicados en `.githooks/` y activados con:

```bash
git config core.hooksPath .githooks
```

## 📌 Avances realizados
[x] Modularización por dominio (productos, carrito, orden, auth_api)

[x] Autenticación JWT con registro y autologin

[x] Documentación Swagger agrupada por tags personalizados

[x] Webhook de email al crear orden

[x] Pruebas automáticas por módulo

[x] Configuración desacoplada con .env

[x] Checklist técnico y documentación por app

## 🚀 Próximos pasos sugeridos
[ ] Vista personalizada de login con JWT

[ ] Roles y permisos avanzados por tipo de usuario

[ ] Conexión a PostgreSQL o MySQL en producción

[ ] Despliegue en Render / Railway / Vercel

[ ] Integración frontend (React + Vite)

[ ] Tests de integración y cobertura con Pytest

## 🧑‍💻 Autor
Nicolás Andrés Cano Leal — Backend Developer especializado en APIs robustas con Django REST Framework, FastAPI y Flask.

“Una tienda simple hecha con principios sólidos: escalabilidad, seguridad y código limpio.”

nicolasandres.pythonanywhere.com
github.com/nicolasandrescl
linkedin.com/in/nicolas-andres-cano-leal
nicolas.cano.leal@gmail.com
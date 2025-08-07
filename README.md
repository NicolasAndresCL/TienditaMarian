# 🛍️ Tiendita de Marian
Tiendita de Marian es una tienda en línea construida con Django + Django REST Framework. Ofrece una API robusta, segura y modular para la gestión de productos, usuarios y compras. Incluye autenticación JWT, carrito persistente, checkout, historial de órdenes, notificaciones por email, documentación OpenAPI decorada sin warnings, y pruebas automáticas por dominio.

## 📦 Tech Stack
Componente	        |Tecnología / Herramienta
--------------------|------------------------------
🧠 Backend	        |Django 5 + Django REST Framework
🔐 Autenticación	  |JWT (djangorestframework-simplejwt)
📘 Documentación	  |Swagger/OpenAPI (drf-spectacular)
🔒 Seguridad	      |.env con python-decouple
🧪 Testing	        |TestCase por módulo
🗄️ Base de datos	    |SQLite (dev) / MySQL o PostgreSQL (producción)
🚀 Despliegue	      |pythonanywhere

## ⚙️ Instalación
```bash
git clone https://github.com/tuusuario/tiendita-marian.git
cd tiendita-marian
python -m venv env
source env/bin/activate  # en Windows: env\Scripts\activate
pip install -r requirements.txt
```
## 🔐 Configuración
Crea un archivo .env en la raíz del proyecto:
```
.env
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
- La API incluye endpoints para login, refresh y registro de usuarios con validaciones y autologin.

Endpoints
- POST /api/auth/register/ → Registra un nuevo usuario y devuelve el token automáticamente

- POST /api/auth/token/ → Autentica y devuelve el token JWT

- POST /api/auth/token/refresh/ → Refresca el token

- Validaciones
- Email único

- Contraseñas coincidentes

- Longitud mínima de contraseña

Ejemplo de respuesta
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

- Carrito persistente por usuario (añadir, eliminar, actualizar)

- Checkout y creación de órdenes

- Historial de órdenes paginado y filtrable

- Detalle de orden específica

- Endpoints protegidos con JWT

- Webhook: email automático al crear orden

- Documentación Swagger decorada por dominio

- Pruebas automáticas por módulo

- Backend modular, desacoplado y listo para producción

- Admin interface habilitada

## 🧱 Estructura del proyecto
```bash
tiendita-backend-django/
├── config/                  # Configuración global del proyecto
│   ├── settings.py          # Configuración con .env, JWT, email, CORS
│   ├── urls.py              # URLs globales por dominio
│   ├── checklist.md         # Tareas técnicas y próximos pasos
│   └── README_SETTING.md    # Documentación específica de configuración
│
├── apps/                    # Apps modulares por dominio
│   ├── productos/           # CRUD de productos
│   ├── carrito/             # Lógica de carrito y checkout
│   ├── orden/               # Gestión de órdenes y señales
│   ├── auth_api/            # Autenticación y registro
│   └── ...                  # Otros módulos futuros
│
├── staticfiles/             # Archivos estáticos recolectados
├── media/                   # Imágenes subidas por usuarios
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

## 📜 Documentación Swagger
```bash
python manage.py generate_swagger
```
- Disponible en /api/docs/ con agrupación por tags, ejemplos, responses y nombres semánticos (operation_id).

- 🪝 Git Hooks personalizados
Este proyecto incluye hooks versionables para automatizar tareas:

- post-checkout: selecciona automáticamente el entorno .env según la rama (main o dev)

- Ubicados en .githooks/ y activados con:

```bash
git config core.hooksPath .githooks
```
## 📌 Avances realizados

✅ Modularización por dominio ✅ Autenticación JWT con registro y autologin ✅ Documentación Swagger decorada por tags ✅ Webhook de email al crear orden ✅ Pruebas automáticas por módulo ✅ Configuración desacoplada con .env ✅ Checklist técnico y documentación por app

## 🚀 Próximos pasos sugeridos
🔲 Vista personalizada de login con JWT 🔲 Roles y permisos avanzados por tipo de usuario 🔲 Conexión a PostgreSQL o MySQL en producción 🔲 Despliegue en Render / Railway / Vercel 🔲 Integración frontend (React + Vite) 🔲 Tests de integración y cobertura con Pytest

## 🧑‍💻 Autor
Nicolás Andrés Cano Leal Backend Developer especializado en APIs robustas con Django REST Framework, FastAPI y Flask.

>“Una tienda simple hecha con principios sólidos: escalabilidad, seguridad y código limpio.”

- 🌐 nicolasandres.pythonanywhere.com

- 🐙 github.com/nicolasandrescl

- 💼 linkedin.com/in/nicolas-andres-cano-leal

- 📧 nicolas.cano.leal@gmail.com

# 🛍️ Tiendita de Marian

**Tiendita de Marian** es una tienda en línea creada con Django y Django REST Framework. Ofrece una API robusta y segura para la gestión de productos, incluyendo autenticación JWT, buenas prácticas en seguridad y despliegue listo para producción.

---

## 📦 Tech Stack

- **Backend**: Django + Django REST Framework
- **Autenticación**: JWT (`djangorestframework-simplejwt`)
- **Seguridad**: Variables protegidas con `.env` (`python-decouple`)
- **Estilo**: Grid responsiva con Flexbox
- **Versionado**: Git
- **Base de datos**: SQLite (desarrollo)

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

- Crear, listar, actualizar y eliminar productos

- JWT auth con access y refresh tokens

- Backend modular y producción-ready

- Admin interface habilitada para gestión rápida

- Visualización responsiva en frontend con Flexbox
---
## 🧱 Estructura del proyecto

```tiendita_marian/
├── productos/                        # App principal de productos
│   ├── migrations/
│   ├── templates/
│   │   └── productos/
│   │       └── index.html           # Vista pública con productos
│   ├── static/
│   │   └── productos/               # Archivos estáticos (si aplica)
│   │       ├── css                                                     
│   │       │   └── style.css     
│   │       └── img
│   ├── admin.py                     # Registro de modelos
│   ├── apps.py
│   ├── models.py                    # Modelo Producto
│   ├── serializers.py               # DRF Serializers
│   ├── views.py                     # API y vistas basadas en clase
│   ├── urls.py                      # Rutas específicas de la app
│   └── tests.py
│
├── ventas_api/                      # Configuración global del proyecto
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                  # Configuración con .env + JWT
│   ├── urls.py                      # URLs globales
│   └── wsgi.py / asgi.py
│
│
├── staticfiles/                     # Static files recolectados (¡ignorar en Git!)
│
├── manage.py
├── .env                             # Variables sensibles (no versionar)
├── requirements.txt                 # Todas las Instalaciones necesarias
├── .gitignore                       # Ignora env, .env, staticfiles, etc.
├── checklist.md                     # Guía de pasos realizados
└── README.md                        # Documentación del proyecto
```
---
## 📌 Próximos pasos

[ ] Vista personalizada de login con JWT

[ ] Sistema de carrito de compras

[ ] Roles y permisos por tipo de usuario

[ ] Conexión a PostgreSQL

[ ] Despliegue (Render / Railway / Vercel)

---

## 🧑‍💻 Autor
Nicolás Andrés Cano Leal Backend Developer especializado en APIs robustas con Django REST Framework y FastAPI.

“Una tienda simple hecha con principios sólidos: escalabilidad, seguridad y código limpio.”


---

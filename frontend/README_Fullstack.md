## 🛍️ Tiendita de Marian

Tiendita de Marian es una tienda virtual desarrollada como proyecto fullstack con Django REST Framework en el backend y React + Vite en el frontend. El objetivo es ofrecer un catálogo de productos con imágenes, stock, precios y una experiencia responsive y atractiva.
---
## 🧱 Estructura del Proyecto

```TienditaMarianFullstack/
├── tiendita-backend/
│   ├── ventas_api/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── ...
│   ├── productos/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── ...
│   ├── media/          ← Imágenes subidas
│   ├── staticfiles/    ← Archivos estáticos recolectados
│   ├── manage.py
│   └── README.md
│
└── tiendita-frontend/
    ├── public/
    ├── src/
    │   ├── App.jsx
    │   ├── main.jsx
    │   ├── components/
    │   │   └── ProductoCard.jsx
    ├── .env
    ├── package.json
    ├── vite.config.js
    └── README.md
```
---
## ⚙️ Instalación y configuración del backend

Instalar dependencias (usando pip o pipenv):

```bash
pip install -r requirements.txt
Variables de entorno (.env):
```
```env
SECRET_KEY=tu_clave_secreta
DATABASES_USER=tu_usuario_mysql
DATABASES_PASSWORD=tu_contraseña_mysql
Configurar base de datos MySQL en settings.py
```
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'tiendita_marian',
        'USER': config('DATABASES_USER'),
        'PASSWORD': config('DATABASES_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```
---
## Migraciones y superusuario:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
---
## Correr servidor local:

```bash
python manage.py runserver
```
Acceder al panel de administración: http://127.0.0.1:8000/admin

Documentación Swagger: http://127.0.0.1:8000/api/docs/
---
## 🧑‍🎨 Instalación y configuración del frontend

Instalar dependencias (Vite + React + Tailwind + Shadcn):

```bash
npm install
```
Archivo .env:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Levantar servidor de desarrollo:

```bash
npm run dev
```

Acceder al frontend local: http://localhost:5173
---
## 🧩 Tecnologías utilizadas

Backend

+ Django 5.2.4

+ Django REST Framework

+ JWT con rest_framework_simplejwt

+ drf-spectacular (Swagger/OpenAPI)

+ MySQL

+ CORS headers

Frontend

+ React

+ Vite

+ TailwindCSS

+ Shadcn/UI

+ Axios

+ ESLint
---
## 🎨 Componentes destacados

- ProductoCard.jsx: renderiza cada producto con imagen, nombre, precio, stock y botón de acción.

- Estilos modulados con Tailwind para fondo pastel, layout responsivo y hover effects.

- Comunicación API vía Axios y variables .env.
---
## 📦 Consideraciones

Backend protegido por JWT, con permisos configurables.

Las imágenes se sirven vía MEDIA_URL usando rutas absolutas desde DRF.

El frontend está preparado para escalar con lógica de carrito, modales, y vista de checkout.
---
## 🚀 Autor
Nicolás Andrés Cano Leal Desarrollador Backend | Especialista en Django REST Framework 📁 Portafolio: nicolasandrescl.pythonanywhere.com
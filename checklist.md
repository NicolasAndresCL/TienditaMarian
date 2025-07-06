# ✅ Django + DRF Project Setup Checklist

Este checklist refleja todos los pasos realizados hasta ahora en el proyecto **Tiendita de Marian** para ayudarte a repetir y escalar la estructura de un backend profesional.

---

## 📁 1. Inicialización del Proyecto

- [x] Crear entorno virtual con `venv` y activarlo
- [x] Instalar Django y DRF con pip
- [x] Crear proyecto con `django-admin startproject`
- [x] Crear app principal (ej. `productos`) con `startapp`
- [x] Añadir app a `INSTALLED_APPS` en `settings.py`

---

## 🛠️ 2. Modelado y Base de Datos

- [x] Crear el modelo `Producto` en `productos/models.py`
- [x] Ejecutar `python manage.py makemigrations`  
- [x] Ejecutar `python manage.py migrate`
- [x] Registrar el modelo en `admin.py`
- [x] Verificar que aparezca en el panel admin

---

## 🎨 3. Frontend básico y layout

- [x] Crear plantilla `index.html` para mostrar productos
- [x] Estilizar productos en una grilla con Flexbox
- [x] Corregir layout CSS para visualización horizontal

---

## 🧪 4. Vistas y Routing con DRF

- [x] Crear vista API para listar productos
- [x] Proteger vistas con `IsAuthenticated`
- [x] Mapear rutas en `urls.py` de app y proyecto

---

## 🔐 5. Autenticación y Seguridad

- [x] Instalar `djangorestframework-simplejwt`
- [x] Configurar JWT como sistema de autenticación en `settings.py`
- [x] Agregar endpoints:
  - `/api/token/` para obtener tokens
  - `/api/token/refresh/` para renovarlos
- [x] Reemplazar autenticación básica por JWT

---

## 🧾 6. Protección de variables sensibles

- [x] Generar nueva `SECRET_KEY` con Django shell
- [x] Crear `.env` y mover `SECRET_KEY` allí
- [x] Instalar `python-decouple`
- [x] Leer `SECRET_KEY` desde `.env` en `settings.py`
- [x] Agregar `.env` al archivo `.gitignore`

---

## 🧰 7. Git y versionado

- [x] Ejecutar `git init`
- [x] Configurar `.gitignore` con:
  - `.env`, `env/`, `__pycache__/`, `.vscode/`, `*.sqlite3`, `staticfiles/`


---

## 📚 8. Documentación de progreso

- [x] Crear commits atómicos por cada paso clave (`feat`, `fix`, `style`, `chore`, `docs`)
- [x] Redactar un commit general que resuma todo el avance:


---

## 🚀 Siguientes pasos sugeridos

- [ ] Crear vista personalizada de login con JWT para frontend
- [ ] Implementar sistema de carrito de compras (`feature/cart`)
- [ ] Incorporar roles de usuario para control de permisos
- [ ] Conectar base de datos PostgreSQL para producción
- [ ] Desplegar en hosting (Render, Railway o similar)

---

> _“Un proyecto sólido se construye con buenas prácticas desde el primer commit.”_


# 🛍️ Tiendita de Marian – Frontend

**Tiendita de Marian** es una aplicación React desarrollada con Vite, TailwindCSS y Shadcn/UI para mostrar productos en una tienda online. Esta interfaz consume una API REST construida en Django, permitiendo visualizar imágenes, precios, stock y botones de acción en una experiencia moderna y responsiva.

---

## ⚙️ Tecnologías utilizadas

- **React** – Librería principal para construir la UI
- **Vite** – Build tool ultra rápido con soporte moderno
- **TailwindCSS** – Utilidades de estilo para diseño limpio y responsive
- **Shadcn/UI** – Componentes accesibles y altamente personalizables
- **Axios** – Cliente HTTP para consumir el backend
- **ESLint** – Reglas de estilo y consistencia en código
- **JavaScript (JSX)** – Lenguaje base del proyecto

---

## 📁 Estructura del proyecto

```tiendita-frontend/
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

## 🚀 Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/tu-usuario/tiendita-frontend.git
cd tiendita-frontend
```

2. Instala las dependencias:

```bash
npm install
```
3. Crea el archivo .env en la raíz:

```env
VITE_API_BASE_URL=http://localhost:8000
```
4. Ejecuta el servidor local:

```bash
npm run dev
```

## 📡 Consumo de API

El frontend se comunica con el backend mediante Axios, apuntando a /api/productos/ para obtener el listado de productos. La URL base se obtiene dinámicamente desde .env usando:

```js
import.meta.env.VITE_API_BASE_URL
```
---
## 🧸 Componente destacado

```<ProductoCard />
```

Este componente muestra cada producto con:

+ Imagen centrada y bien enfocada

+ Nombre del producto

+ Precio en formato claro

+ Stock disponible

+ Botón “Agregar al carrito” con ícono y estilo visual

Estilos aplicados con Tailwind y fondos pastel que reflejan la identidad visual de la tienda.

## 🎨 Personalización visual

La aplicación usa una paleta de colores amigable y coherente:

- bg-violet-100: fondo general

- bg-rose-100: cards de productos

- text-pink-700, text-gray-800: texto y acentos

- bg-pink-500: botón de acción

Se puede modificar fácilmente desde index.css o envolviendo la app en un <div> con clases globales en main.jsx.

---

## 📦 Por hacer / futuro

+ Lógica de carrito con useContext o localStorage

+ Formato de precio con Intl.NumberFormat

+ Vista de checkout

+ Animaciones y transiciones suaves

+ Rutas protegidas con JWT desde el frontend

---

## 🧑‍💻 Autor
Nicolás Andrés Cano Leal Desarrollador Backend & Fullstack | Especialista en APIs REST 📁 Portafolio: nicolasandrescl.pythonanywhere.com
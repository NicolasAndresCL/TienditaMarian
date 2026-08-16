# Despliegue — Tiendita de Marian

Qué hay que hacer, en qué orden, para sacar la tienda a internet. El **dónde**
—qué proveedor, cuánto cuesta, qué dominio— está en
[`hosting-y-dominio.md`](hosting-y-dominio.md); esto es el **cómo**.

> **Estado a 2026-08-16:** la configuración de producción está lista y verificada,
> pero **no se ha desplegado nada**. Faltan tres decisiones que no son técnicas:
> proveedor, dominio y contrato de comercio con Transbank.

---

## Lo que ya está resuelto

No hay que construir nada de esto, solo configurarlo:

- **Imágenes de producción**: `backend/Dockerfile` (multi-stage, sin root, con
  healthcheck) y `frontend/Dockerfile` (nginx sirviendo el bundle; la imagen final
  no lleva Node ni `node_modules`).
- **Arranque del backend**: su `CMD` ya hace `migrate` → `collectstatic` →
  `gunicorn`. Un proveedor que corra el Dockerfile no necesita nada más.
- **Settings de producción** (`config/settings/prod.py`): HTTPS, HSTS, cookies
  `Secure`, WhiteNoise para estáticos, `ALLOWED_HOSTS` sin default.
- **Verificado que arranca de verdad**: `scripts/humo-produccion.sh` levanta el
  backend con `SECURE_HTTPS=True` y comprueba el comportamiento tras un proxy TLS.
  Corre en el CI, en el job `docker-smoke`.

## Lo que falta, y en qué orden

### 1. Contrato con Transbank — **empezar por aquí**

Es lo único con plazos que no dependen de nosotros. Hoy la tienda cobra contra el
**ambiente de integración**: el flujo se recorre entero, con tarjetas de prueba, y
no se mueve un peso real. Para cobrar de verdad hace falta un contrato de comercio,
y de ahí salen `WEBPAY_COMMERCE_CODE` y `WEBPAY_API_KEY` de producción.

Se puede desplegar sin esto. La tienda funciona, se ve, se navega y se puede
"comprar" — simplemente no cobra. Conviene decidir si eso se abre al público o se
deja en un dominio de pruebas hasta tener el contrato.

### 2. Dominio

`.cl` en NIC Chile o `.com` en Cloudflare Registrar (comparativa y precios en
`hosting-y-dominio.md`). Hace falta antes del punto 4, porque tres variables lo
llevan escrito: `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` y `CORS_ALLOWED_ORIGINS`.

### 3. Almacenamiento de las fotos — **el que se olvida**

**En Render y en Fly el disco es efímero.** Las fotos que Marian suba desde el
admin desaparecen en el siguiente despliegue, sin ningún error: la fila del
producto queda apuntando a un archivo que ya no existe y el catálogo se llena de
imágenes rotas.

Las fotos del catálogo de demostración no tienen ese problema (van dentro de la
imagen), así que el fallo **no se ve al desplegar**: aparece semanas después, la
primera vez que se sube un producto nuevo y se hace un despliegue.

Tres salidas, de menor a mayor trabajo:

| Opción | Cómo | Cuándo conviene |
|---|---|---|
| Volumen persistente del proveedor | Fly (`fly volumes`), Render (disco de pago) | Lo más rápido; ata la tienda a ese proveedor |
| Bucket S3-compatible | `django-storages` + Cloudflare R2 o Backblaze B2 (~$0 a este volumen) | Lo correcto a medio plazo; sirve las fotos por CDN y sobrevive a cambiar de hosting |
| Subir las fotos al repo | `cargar_productos` y commitear | Solo si el catálogo lo mantiene un desarrollador, no Marian |

`SERVE_MEDIA` queda en `False` pase lo que pase: `django.views.static.serve` es
síncrono y no está pensado para tráfico.

### 4. Variables de entorno

La lista exhaustiva, comentada una por una, está en
[`backend/.env.produccion.example`](../backend/.env.produccion.example).

**No se copia como archivo al servidor**: se cargan en el panel del proveedor o
con `fly secrets set`. Un `.env` en el servidor es un archivo más que puede acabar
en un backup o en un log.

Las tres que más veces se equivocan:

- **`CSRF_TRUSTED_ORIGINS`** — desde que la sesión viaja en cookies, Django rechaza
  **toda** escritura cuyo `Origin` no esté aquí. Si falta, se puede navegar el
  catálogo pero no registrarse ni comprar. Va con esquema (`https://`) y sin barra
  final.
- **`CORS_ALLOWED_ORIGINS`** — si no coincide con el dominio del frontend, el
  navegador bloquea cada llamada y la tienda se ve **vacía**, sin ningún error en
  los logs del servidor. Es el fallo más desconcertante de los tres.
- **`SECRET_KEY`** — nueva, distinta de la de desarrollo, y **sin `$`** si se carga
  vía un `.env` leído por docker compose (lo interpola y llega truncada).

### 5. El frontend

`VITE_API_BASE_URL` se **hornea en el bundle en tiempo de build**, no se lee en
ejecución: hay que pasarlo como argumento de build, y **rehacer el build** si el
dominio de la API cambia. Cambiar solo la variable en el panel no hace nada.

En Vercel/Netlify/Cloudflare Pages: build `npm run build`, salida `dist/`, y un
rewrite de todo a `/index.html` para que el router funcione al recargar una ruta
profunda (`/producto/3`). Sin eso, recargar da 404.

### 6. Verificación después de desplegar

En este orden — cada uno descarta una causa distinta:

```bash
curl -si https://api.TUDOMINIO/healthz/ | head -20
# 200 y base_de_datos: ok  → la API vive y ve la base

curl -si http://api.TUDOMINIO/healthz/ | head -3
# 301 a https  → la redirección funciona

curl -si https://api.TUDOMINIO/api/v1/productos/ | head -5
# 200 con productos  → el catálogo responde

curl -si https://api.TUDOMINIO/api/schema/swagger-ui/ | head -3
# 200  → los estáticos comprimidos y el manifiesto están bien
```

Y en el navegador, que es donde aparece lo que curl no ve:

1. Abrir la tienda y comprobar que **se ven las fotos** (si no: punto 3).
2. Registrarse. Si da 403, es `CSRF_TRUSTED_ORIGINS`.
3. Si el catálogo se ve vacío sin errores en el servidor, es `CORS_ALLOWED_ORIGINS`
   — la pista está en la consola del navegador, no en los logs.
4. Comprar algo y confirmar que llega el correo (si no: dominio del remitente sin
   verificar en el proveedor de correo, o el mail cayó en spam).
5. Pagar con Webpay y comprobar que vuelve a `?pago=pagado`.

### 7. Antes de abrir al público

- [ ] `python manage.py createsuperuser` en producción, con clave fuerte.
- [ ] Comprobar que `/admin/` pide sesión y que Marian puede entrar.
- [ ] Backups de la base activados (Neon los trae; en otros hay que encenderlos).
- [ ] Cargar el catálogo real, no el de demostración.
- [ ] Decidir qué pasa con las órdenes de prueba que queden en la base.

---

## Si algo se cae

`docker compose logs backend` en local; en el proveedor, su visor de logs. Los
errores de negocio salen como `WARNING` con su código
(`stock_insuficiente`, `orden_ya_pagada`); los `ERROR` con traceback son bugs
de verdad y hay que mirarlos.

El fallo con peor relación entre gravedad y visibilidad es el **bucle de
redirecciones**: si la aplicación no reconoce `X-Forwarded-Proto`, redirige a
https, el proxy vuelve a entrar por http, y el sitio queda caído con
`check --deploy` en verde. Para eso existe `scripts/humo-produccion.sh`, y por eso
corre en el CI.

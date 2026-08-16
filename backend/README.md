# 🧸 Tiendita de Marian — Backend

API REST de una tienda en línea real, construida con **Django 6.1 + DRF + JWT +
PostgreSQL**: catálogo, carrito, checkout transaccional, órdenes, pagos, envíos,
descuentos, reseñas y auditoría de eventos.

---

## Arranque rápido

```bash
python -m venv env && env/Scripts/activate       # Windows
pip install -r requirements/dev.txt

cp .env.example .env
# Generar una SECRET_KEY y ponerla en el .env:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- API → <http://127.0.0.1:8000/api/v1/>
- Documentación → <http://127.0.0.1:8000/api/schema/swagger-ui/>
- Salud → <http://127.0.0.1:8000/healthz/>

### Con Docker (PostgreSQL + MailHog)

Este `backend/` es parte del monorepo TienditaMarian. El `docker-compose.yml` vive
en la **raíz** del monorepo y levanta todo (backend + frontend + PostgreSQL +
MailHog):

```bash
cd ..            # a la raíz del monorepo
docker compose up --build
```

MailHog queda en <http://localhost:8025>, donde caen los mails de confirmación de
compra. El runbook completo está en [`../pasos.md`](../pasos.md).

---

## Arquitectura

Capas con una única dirección de dependencia (`apps` → `core`, nunca al revés).
La regla de oro: **una decisión de negocio debe poder probarse sin abrir una red
ni una base de datos.**

```
config/settings/     base · dev · prod · test   (test HEREDA de base)
core/                excepciones de dominio · eventos · permisos · vistas base
apps/<dominio>/
    models.py        datos e invariantes
    selectors.py     lectura (querysets sin N+1)
    services.py      reglas de negocio
    serializers.py   entrada/salida
    views.py         orquestación HTTP
```

**Decisión de diseño (ADR-001):** la API usa `GenericAPIView` + mixins en vez de
`ViewSets` + router. Es una elección deliberada: hay endpoints que no son CRUD
(`/checkout/`, `/carrito/items/cantidad/`, `/carrito/vaciar/`) y no calzan en las
acciones de un router. La duplicación que ese patrón suele arrastrar se resuelve
por herencia, en `core/api/base_views.py`, donde los verbos HTTP se escriben una
sola vez y cada app declara solo lo suyo.

### Formato de errores

Todos los errores salen con la misma forma, y con un `codigo` estable para que el
frontend reaccione a un identificador y no a un texto en español:

```json
{
  "error": {
    "codigo": "stock_insuficiente",
    "mensaje": "No alcanza el stock de «Muñeca»: pediste 3 y quedan 2.",
    "detalle": { "producto": "Muñeca", "solicitado": 3, "disponible": 2 }
  }
}
```

`stock_insuficiente` responde **409**, no 400: la petición está bien formada; lo
que cambió es el inventario.

---

## El flujo de compra

`CheckoutService` (`apps/carrito/services.py`) hace todo esto dentro de **una**
transacción — si algo falla, se revierte entero:

1. Bloquea las filas de producto (`select_for_update`) para cerrar la carrera por
   la última unidad entre dos clientas que compran a la vez.
2. Valida el stock disponible.
3. Aplica el cupón, si viene.
4. Crea la orden y **congela el precio** en cada ítem: si mañana sube, esa orden
   conserva el precio que se pagó.
5. Descuenta el inventario.
6. Vacía el carrito.
7. Ya confirmada la transacción, emite `ORDEN_CREADA`: correo de confirmación,
   notificación y envío pendiente.

Los efectos del paso 7 son suscriptores desacoplados (`core/events.py`): si el
servidor de correo está caído, la venta ya ocurrió y queda registrada igual.

Si el paso 2 falla, la transacción revierte y `ejecutar()` emite `STOCK_AGOTADO`
—aviso de venta perdida al staff— **fuera** del bloque transaccional. Tiene que
ser fuera: un suscriptor que escribiera en la base desde dentro vería su trabajo
revertido junto con la orden que nunca existió, sin dar ningún error. Y aquí
`on_commit` no sirve de nada, porque este camino nunca llega a hacer commit.

### El cobro

`POST /api/v1/ordenes/<id>/pagar/` delega en `PagoService`, que bloquea la fila
de la orden, cobra con la pasarela configurada, registra el `Pago`, marca la
orden y emite `ORDEN_PAGADA` (correo de confirmación + notificación). Es
**idempotente**: reintentarlo sobre una orden ya pagada devuelve 409
`orden_ya_pagada`, nunca un segundo cobro.

### Webpay Plus

Hay dos formas de cobrar, y son abstracciones distintas porque el dinero se
mueve distinto:

| | `PasarelaPago` | `PasarelaRedirigida` |
|---|---|---|
| Cómo cobra | en una llamada | en dos pasos, con una visita a otro sitio |
| Quién la implementa | `PagoManual` (transferencia) | `PagoWebpay` (Transbank) |
| Endpoint | `POST /ordenes/<id>/pagar/` | `POST /ordenes/<id>/pagar/webpay/` |

El flujo de Webpay:

```
1. POST /ordenes/<id>/pagar/webpay/   → { url, token }   ← con sesión
2. el navegador va a `url` por POST con `token_ws`
3. la clienta paga en Transbank
4. POST /pagos/webpay/retorno/        ← SIN sesión, desde el dominio de Transbank
5. redirección a /compra/<id>?pago=pagado|rechazado|anulado
```

**El paso 4 es público a propósito, y no es negociable**: Transbank devuelve el
control con un POST desde su dominio, y una cookie `SameSite=Lax` no viaja en un
POST cross-site. Si ese endpoint exigiera sesión, ningún pago podría confirmarse
jamás. Lo que lo autentica es el `token_ws`: un secreto de un solo uso que solo
está en el servidor de Transbank y en nuestra fila de `Pago`.

Una transacción se da por buena **solo** si `response_code == 0` **y**
`status == "AUTHORIZED"`. Comprobar una sola de las dos daría por pagada una que
no lo está.

Las credenciales del ambiente de integración son públicas (las trae el propio
SDK), así que se puede desarrollar y probar el flujo completo sin contrato de
comercio. En producción se definen `WEBPAY_COMMERCE_CODE`, `WEBPAY_API_KEY` y
`WEBPAY_PRODUCCION=True`.

**Defensa en profundidad del inventario:** `select_for_update` protege desde la
aplicación y un `CheckConstraint` de `stock >= 0` protege desde la base. Esa
última barrera no puede saltársela ningún código.

---

## Endpoints (v1)

| Método | Ruta | Acceso |
|---|---|---|
| `GET` | `/api/v1/productos/` · `/<id>/` | público |
| `POST` `PUT` `PATCH` `DELETE` | `/api/v1/productos/…` | **staff** |
| `GET` | `/api/v1/carrito/` | sesión |
| `POST` | `/api/v1/carrito/items/` | sesión |
| `PATCH` | `/api/v1/carrito/items/cantidad/` | sesión |
| `DELETE` | `/api/v1/carrito/items/quitar/` · `/carrito/vaciar/` | sesión |
| `POST` | `/api/v1/checkout/` | sesión |
| `GET` | `/api/v1/ordenes/` · `/<id>/` | dueño |
| `POST` | `/api/v1/ordenes/<id>/pagar/` · `/pagar/webpay/` | dueño |
| `POST` `GET` | `/api/v1/pagos/webpay/retorno/` | **público** (lo llama Transbank) |
| `GET` `POST` | `/api/v1/envios/` · `/api/v1/pagos/` | dueño |
| `GET` | `/api/v1/reviews/` | público |
| `POST` `PATCH` `DELETE` | `/api/v1/reviews/…` | autor |
| `GET` `POST` | `/api/v1/descuentos/` | lectura: sesión · escritura: **staff** |
| `GET` | `/api/v1/analytics/` | **staff** |
| `POST` | `/api/v1/auth/{token,token/refresh,register,logout}/` | público |
| `GET` | `/api/v1/auth/me/` | sesión |

### Autenticación

Dos vías, y la aplicación usa la primera:

- **Cookies `HttpOnly`** (el navegador). El login y el registro dejan la sesión
  en `tiendita_access` (15 min) y `tiendita_refresh` (7 días), invisibles para el
  JavaScript de la página: un XSS ya no puede robar la sesión. Como el navegador
  las manda solo, las peticiones que escriben exigen el token **CSRF** en la
  cabecera `X-CSRFToken`.
- **`Authorization: Bearer <access>`** (Swagger, scripts, clientes de API). El
  `access` sigue viniendo en el cuerpo del login para esto. Por esta vía no se
  pide CSRF: quien pone la cabecera a mano ya demuestra que controla la petición.

El refresh rota en cada uso y el `logout` lo invalida de verdad (blacklist)
además de borrar las cookies. `/auth/me/` existe porque el frontend ya no puede
mirar el token para saber si hay sesión: lo pregunta.

> Las rutas antiguas (`/api/productos/productos/`, `/api/carrito/carrito/add/`…)
> convivieron con estas mientras el frontend migraba y **ya se eliminaron**: hoy
> devuelven 404 y un test lo verifica.

---

## Tests

```bash
pytest                            # 188 tests · 92 % de cobertura
pytest --cov                      # con cobertura
ruff check .                      # lint
python manage.py check --deploy   # hardening de producción
```

La configuración de tests **hereda** de la de producción (`config/settings/test.py`
← `base.py`): los mismos `INSTALLED_APPS`, la misma autenticación JWT y los mismos
permisos. Si un test pasa aquí, pasa contra la aplicación que se despliega.

⚠️ El test de concurrencia del checkout **se salta en SQLite**: ese motor ignora
`select_for_update`, así que el test pasaría sin probar nada. El CI levanta un
PostgreSQL para ejecutarlo de verdad. En local, desde la raíz del monorepo:

```bash
cd ..
docker compose --profile test run --rm tests
```

El servicio `tests` construye el target `dev` del `Dockerfile`, que es el único que
instala `requirements/dev.txt`. Contra el servicio `backend` daría `pytest: not
found`: su imagen es la de producción.

---

## Seguridad

- **La sesión no es accesible desde JavaScript**: los JWT viajan en cookies
  `HttpOnly`, no en `localStorage`. Con ello la API pasa a ser vulnerable a CSRF,
  así que se exige el token CSRF en toda escritura autenticada por cookie.
- JWT con access corto (15 min), rotación de refresh y blacklist al cerrar sesión.
- Throttling diferenciado: anónimo (60/min), usuario (300/min) y **login (10/min)**,
  que es el endpoint que se ataca por fuerza bruta.
- Los validadores de contraseña de Django se aplican en el registro.
- Autorización a nivel de objeto: nadie ve ni toca los datos de otra clienta.
- Auditoría con lista blanca de modelos y campos sensibles filtrados.
- `manage.py check --deploy` limpio (SSL, HSTS, cookies seguras), verificado en CI.

## Stack

Django 6.1 · DRF 3.18 · SimpleJWT · drf-spectacular · PostgreSQL (psycopg 3) ·
pytest · ruff · Docker · GitHub Actions

---

Autor: **Nicolás Andrés Cano Leal** · Licencia MIT

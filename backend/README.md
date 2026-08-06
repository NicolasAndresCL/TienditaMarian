# 🧸 Tiendita de Marian — Backend

API REST de una tienda en línea real, construida con **Django 5.2 + DRF + JWT +
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

```bash
docker compose up --build
```

Levanta la base, el backend y un buzón de correo en <http://localhost:8025>, donde
caen los mails de confirmación de compra.

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
| `GET` `POST` | `/api/v1/envios/` · `/api/v1/pagos/` | dueño |
| `GET` | `/api/v1/reviews/` | público |
| `POST` `PATCH` `DELETE` | `/api/v1/reviews/…` | autor |
| `GET` `POST` | `/api/v1/descuentos/` | lectura: sesión · escritura: **staff** |
| `GET` | `/api/v1/analytics/` | **staff** |
| `POST` | `/api/v1/auth/{token,token/refresh,register,logout}/` | público |

Autenticación: `Authorization: Bearer <access>`. El access dura 15 minutos, el
refresh rota, y el `logout` lo invalida de verdad (blacklist).

> Las rutas antiguas (`/api/productos/productos/`) siguen respondiendo mientras se
> migra el frontend, y se eliminarán después.

---

## Tests

```bash
pytest                            # 121 tests
pytest --cov                      # con cobertura
ruff check .                      # lint
python manage.py check --deploy   # hardening de producción
```

La configuración de tests **hereda** de la de producción (`config/settings/test.py`
← `base.py`): los mismos `INSTALLED_APPS`, la misma autenticación JWT y los mismos
permisos. Si un test pasa aquí, pasa contra la aplicación que se despliega.

⚠️ El test de concurrencia del checkout **se salta en SQLite**: ese motor ignora
`select_for_update`, así que el test pasaría sin probar nada. El CI levanta un
PostgreSQL para ejecutarlo de verdad. En local:

```bash
docker compose run --rm backend pytest -rs
```

---

## Seguridad

- JWT con access corto (15 min), rotación de refresh y blacklist al cerrar sesión.
- Throttling diferenciado: anónimo (60/min), usuario (300/min) y **login (10/min)**,
  que es el endpoint que se ataca por fuerza bruta.
- Los validadores de contraseña de Django se aplican en el registro.
- Autorización a nivel de objeto: nadie ve ni toca los datos de otra clienta.
- Auditoría con lista blanca de modelos y campos sensibles filtrados.
- `manage.py check --deploy` limpio (SSL, HSTS, cookies seguras), verificado en CI.

## Stack

Django 5.2 · DRF 3.16 · SimpleJWT · drf-spectacular · PostgreSQL (psycopg 3) ·
pytest · ruff · Docker · GitHub Actions

---

Autor: **Nicolás Andrés Cano Leal** · Licencia MIT

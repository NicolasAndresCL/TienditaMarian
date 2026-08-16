# Pasos — Tiendita de Marian

Runbook de comandos para levantar, probar y desplegar el monorepo: `backend/`
(Django 5.2 + DRF + JWT + PostgreSQL) y `frontend/` (React 19 + Vite 7 + Tailwind 4).

Todos los comandos están verificados contra los archivos reales del repo
(`backend/README.md`, `backend/CLAUDE.md`, `backend/pyproject.toml`,
`backend/manage.py`, `backend/config/settings/*.py`, `docker-compose.yml` —el de
la **raíz**, que orquesta el monorepo completo—, `backend/Dockerfile`,
`frontend/package.json`). Se muestran en PowerShell y en bash cuando difieren.

---

## Índice

1. [Requisitos previos](#1-requisitos-previos)
2. [Levantar en local sin Docker](#2-levantar-en-local-sin-docker)
3. [Levantar en local con Docker (recomendado)](#3-levantar-en-local-con-docker-recomendado)
4. [Tests y calidad](#4-tests-y-calidad)
5. [Migrar de SQLite a PostgreSQL en local](#5-migrar-de-sqlite-a-postgresql-en-local)
6. [Desplegar en la web](#6-desplegar-en-la-web)
7. [Comandos útiles](#7-comandos-útiles)

---

## 1. Requisitos previos

| Herramienta | Versión mínima | Por qué |
|---|---|---|
| Python | 3.12+ | Backend (Django 5.2, `ruff` apunta a `py312`, imagen Docker `python:3.12-slim`) |
| Node.js | 20+ | Frontend (Vite 7, React 19) |
| Docker + Docker Compose | reciente | Camino recomendado; obligatorio para el test de concurrencia del checkout |
| PostgreSQL | 16 (opcional en local) | Solo si no usás Docker y querés Postgres en vez de SQLite |

Verificar versiones instaladas:

```powershell
python --version
node --version
npm --version
docker --version
docker compose version
```

```bash
python3 --version
node --version
npm --version
docker --version
docker compose version
```

---

## 2. Levantar en local sin Docker

### Backend

```powershell
cd c:\dev\projects\refactoring\TienditaMarian\backend
python -m venv env
env\Scripts\activate
pip install -r requirements\dev.txt

copy .env.example .env
```

```bash
cd TienditaMarian/backend
python3 -m venv env
source env/bin/activate
pip install -r requirements/dev.txt

cp .env.example .env
```

Generar una `SECRET_KEY` real y pegarla en `.env` (el `.env.example` trae un
valor de relleno que **no** sirve para nada real):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> ⚠️ **Cuidado con el BOM en PowerShell.** Si editás `.env` desde PowerShell con
> `Set-Content -Encoding utf8` o `Add-Content`, PowerShell antepone un BOM
> (byte-order mark) que `django-environ` no sabe parsear: la primera variable
> del archivo queda ilegible y Django falla con `SECRET_KEY` no encontrada.
> Editá `.env` con un editor de texto normal (VS Code, Notepad++) en vez de
> reescribirlo desde la terminal. Si necesitás generarlo por script, usá:
> ```powershell
> [System.IO.File]::WriteAllLines(
>     "$PWD\.env",
>     (Get-Content .env.example),
>     (New-Object System.Text.UTF8Encoding($false))
> )
> ```
> (`UTF8Encoding($false)` = UTF-8 **sin** BOM.)

El resto de `.env` (además de `SECRET_KEY`) ya trae valores razonables para
desarrollo: `DEBUG=True`, `DATABASE_URL` con SQLite si se comenta la línea de
Postgres (ver §5), `CORS_ALLOWED_ORIGINS` apuntando al Vite de `:5173` y
`EMAIL_BACKEND` de consola (los correos se imprimen en la terminal).

> ⚠️ **`backend/.env` y el `.env` de la raíz NO son intercambiables.** El de la
> raíz alimenta la interpolación `${...}` de `docker-compose.yml`; este lo lee
> `django-environ` cuando Django corre **sin** Docker. Copiar uno sobre el otro
> deja el backend local apuntando a `DATABASE_URL=postgres://…@db:5432/…`, y `db`
> es el nombre del servicio de Compose: solo resuelve dentro de su red. El
> síntoma es `failed to resolve host 'db'` al primer `migrate`. Sin Docker el
> host va en `localhost`.

Migrar, crear superusuario, cargar el catálogo de demostración y arrancar:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py cargar_productos
python manage.py runserver
```

`cargar_productos` lee `apps/productos/fixtures/productos.csv` y busca las
imágenes en `media/productos/images/`; crea los productos que falten y avisa
(sin duplicar) los que ya existen.

- API → <http://127.0.0.1:8000/api/v1/>
- Documentación (Swagger UI) → <http://127.0.0.1:8000/api/schema/swagger-ui/>
- Salud → <http://127.0.0.1:8000/healthz/>

### Frontend

En otra terminal:

```powershell
cd c:\dev\projects\refactoring\TienditaMarian\frontend
npm install
copy .env.example .env
npm run dev
```

```bash
cd TienditaMarian/frontend
npm install
cp .env.example .env
npm run dev
```

`.env` solo trae `VITE_API_BASE_URL=http://localhost:8000` (todo lo que
empieza con `VITE_` queda embebido en el bundle: nunca va un secreto ahí).
Vite sirve en <http://localhost:5173> y apunta al backend de `:8000`.

---

## 3. Levantar en local con Docker (recomendado)

Es el único camino que ejecuta el checkout con PostgreSQL real (`select_for_update`
funcionando de verdad) y que replica el `gunicorn` + `WhiteNoise` de producción.

Definí un `SECRET_KEY` en un `.env` en la raíz del monorepo (el compose lo exige:
`${SECRET_KEY:?define SECRET_KEY en tu .env}`, sin default por seguridad):

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# pegar el resultado en: TienditaMarian\.env → SECRET_KEY=...
```

> ⚠️ **Escapá los `$` de la clave como `$$`.** Compose interpola `$var` al leer el
> `.env`, así que una clave como `!nsk*$hic2l@…` llega **truncada** al contenedor:
> `$hic2l` se resuelve como una variable vacía y solo queda un warning discreto
> (`The "hic2l" variable is not set`). El `.env` versionado usa a propósito una
> clave sin `$`.

El compose también publica PostgreSQL en el host. Si ya tenés un PostgreSQL
propio en el `5432`, el `up` falla con *port is already allocated*: definí otro
puerto en el `.env` de la raíz (por defecto el repo trae `POSTGRES_PORT=5433`).

Levantar todo desde la raíz del monorepo:

```powershell
cd c:\dev\projects\refactoring\TienditaMarian
docker compose up --build
```

```bash
cd TienditaMarian
docker compose up --build
```

Puertos que quedan expuestos:

| Servicio | URL / puerto | Detalle |
|---|---|---|
| Backend (API) | <http://localhost:8000> | `gunicorn` detrás de `DJANGO_SETTINGS_MODULE=config.settings.prod` |
| Salud | <http://localhost:8000/healthz/> | usado por el `HEALTHCHECK` del `Dockerfile` |
| Frontend | <http://localhost:5173> | SPA estática servida por nginx, construida con `VITE_API_BASE_URL=http://localhost:8000` |
| PostgreSQL | `localhost:5433` | `POSTGRES_PORT` en el `.env` de la raíz; usuario/clave/DB: `tiendita` / `tiendita` / `tiendita_marian` |
| MailHog (correos) | <http://localhost:8025> | ahí caen los correos de confirmación de compra |

Las migraciones y el `collectstatic` **ya corren solos** en el `CMD` del
`backend/Dockerfile`; lo que sí hay que hacer a mano es sembrar el catálogo y
crear la cuenta de administración (no hace falta activar ningún venv):

```bash
docker compose exec backend python manage.py cargar_productos
docker compose exec backend python manage.py createsuperuser
```

Las fotos del catálogo se sirven porque el compose define `SERVE_MEDIA=True` y
monta `./backend/media` dentro del contenedor. Con `DEBUG=False`, Django no
publica `/media/` por su cuenta y WhiteNoise solo sirve los estáticos: sin esas
dos piezas la tienda se ve entera pero sin ni una imagen.

Apagar todo (agregá `-v` si además querés borrar los volúmenes de Postgres y media):

```bash
docker compose down
docker compose down -v   # borra también los datos de la base y el media subido
```

---

## 4. Tests y calidad

### Backend

```powershell
env\Scripts\activate
```

```bash
source env/bin/activate
```

```bash
pytest                            # 188 tests (config en pyproject.toml, settings de test)
pytest --cov                      # con reporte de cobertura
ruff check .                      # lint (E, F, I, UP, B, DJ, C4, T20)
python manage.py check --deploy   # hardening de producción
```

Sobre SQLite pasan 187 y se salta 1: el de concurrencia del checkout.

El CI exige **90 %** de cobertura (`--cov-fail-under=90`); la real es 91,8 %.

### Antes de pushear: reproducir el CI

```bash
./scripts/verificar.sh              # todo
./scripts/verificar.sh backend      # solo backend
./scripts/verificar.sh entorno      # la suite del frontend DENTRO de node:20, sin .env
```

El modo `entorno` reproduce el **checkout del CI**, no solo sus comandos: corre
los tests en una imagen limpia, con `npm ci`, la misma versión de Node y **sin
`frontend/.env`** —que está en `.gitignore` y allí no existe—. Es la única forma
de cazar un fallo que dependa de una variable de entorno que en local sí está.

**Mejor: que lo haga solo.** Hay un hook de `pre-push` que ejecuta esa
verificación y **cancela el push si algo falla**. Se activa una vez por clon:

```bash
git config core.hooksPath .githooks
```

Solo se dispara si el push toca `backend/`, `frontend/`, `scripts/` o el
workflow: un push de documentación no espera a la suite. Y se puede saltar
puntualmente con `git push --no-verify` (por ejemplo, para subir una rama a
medias y ver qué dice el CI).

Corre lo mismo que el pipeline: `ruff`, la suite con el 90 % de cobertura
exigido, el `check --deploy --fail-level WARNING` **contra la configuración de
producción**, y el lint + tests + build del frontend.

Existe porque hubo tres corridas seguidas en rojo por warnings de
drf-spectacular. En local todo "pasaba" —`pytest` y `ruff` en verde— porque el
único job que fallaba era justamente el que nadie ejecutaba a mano. Un paso
obligatorio que hay que acordarse de hacer no es obligatorio: es un
recordatorio.

No cubre el job `docker-smoke`; para eso, lo de abajo.

### Humo del stack completo

Hay una clase de fallos que ningún test unitario ve, porque solo existe en la
frontera entre el código y su entorno: una ruta de estático sensible a
mayúsculas, `/media/` sin servir con `DEBUG=False`, un healthcheck que miente.
Para eso está `scripts/smoke.sh`, que usa la aplicación ya levantada:

```bash
docker compose up --build -d
bash scripts/smoke.sh
```

Comprueba que los tres servicios llegan a *healthy*, siembra el catálogo, y
verifica la API, el Swagger UI, las fotos del catálogo, la SPA y su fallback de
router, más que las rutas v0 sigan en 404. Es el mismo script que corre el job
`docker-smoke` del CI, así que se puede reproducir el pipeline entero en local.

`check --deploy` solo reporta las advertencias de seguridad (HSTS, cookies
seguras, SSL redirect, etc.) que están configuradas en
`config/settings/prod.py`. Corriéndolo con la config de `dev` (la que carga
`manage.py` por defecto) va a avisar de "faltantes" que en desarrollo son
normales; para una verificación real, apuntá a producción primero:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.prod"
python manage.py check --deploy
```

```bash
DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py check --deploy
```

⚠️ **El test de concurrencia del checkout se salta en SQLite**: ese motor
ignora `select_for_update`, así que ahí el test pasaría sin probar nada real.
Para ejecutarlo de verdad hace falta PostgreSQL (Docker):

```bash
docker compose --profile test run --rm tests
```

El servicio `tests` construye el target `dev` del `backend/Dockerfile` y corre
`pytest -rs` contra el PostgreSQL del compose. El flag `-rs` muestra el motivo
del *skip*, de modo que se ve explícitamente que aquí **no** se salta.

> No uses el servicio `backend` para esto: su imagen instala solo
> `requirements/prod.txt` y no lleva pytest (`pytest: not found`). Ese es
> justamente el motivo de que exista el servicio `tests`.

### Frontend

```bash
npm test          # vitest run — 25 tests
npm run test:cov  # vitest run --coverage
npm run lint       # eslint .
npm run build      # vite build → frontend/dist/
```

---

## 5. Migrar de SQLite a PostgreSQL en local

Por defecto, si `DATABASE_URL` no apunta a nada, el backend cae en SQLite
(`sqlite:///db.sqlite3`). Para pasar a Postgres en local sin usar todo el
`docker compose` de la sección 3:

**Opción A — solo el contenedor de Postgres:**

```bash
docker run --name tiendita-postgres -d \
  -e POSTGRES_USER=tiendita \
  -e POSTGRES_PASSWORD=tiendita \
  -e POSTGRES_DB=tiendita_marian \
  -p 5433:5432 \
  postgres:16-alpine
```

**Opción B — solo el servicio `db` del compose del proyecto:**

```bash
docker compose up -d db
```

En ambos casos, editar `backend/.env` y ajustar (es lo que el repo ya trae):

```
DATABASE_URL=postgres://tiendita:tiendita@localhost:5433/tiendita_marian
```

> Se publica en el **5433** y no en el 5432 porque este equipo tiene un PostgreSQL
> nativo ocupando el puerto por defecto. Si el tuyo está libre, podés usar 5432 en
> los dos sitios (`POSTGRES_PORT` en el `.env` de la raíz y aquí).

Migrar y (opcionalmente) recargar el catálogo, ya que es una base nueva y vacía:

```bash
python manage.py migrate
python manage.py cargar_productos
python manage.py createsuperuser
```

---

## 6. Desplegar en la web

Pasos genéricos, sin atarse a un proveedor concreto (Render, Railway, Fly.io,
un VPS propio, etc.). Para el **dónde** específico (dominio, proveedor,
DNS), ver [`docs/hosting-y-dominio.md`](docs/hosting-y-dominio.md).

### Backend

1. **Construir la imagen** (multi-stage, corre sin root, ya trae `gunicorn` +
   `WhiteNoise` + `HEALTHCHECK`):

   ```bash
   docker build -t tiendita-backend ./backend
   ```

2. **Variables de entorno de producción** (el proceso falla rápido si faltan
   las obligatorias, por diseño — mejor que arrancar mal configurado):

   | Variable | Obligatoria | Notas |
   |---|---|---|
   | `SECRET_KEY` | sí | generarla con el comando de la sección 2, una distinta por entorno |
   | `DATABASE_URL` | sí | `postgres://usuario:password@host:5432/db` (psycopg 3) |
   | `ALLOWED_HOSTS` | sí | sin default en `prod.py`, a propósito — ej. `tienditademarian.com,www.tienditademarian.com` |
   | `CORS_ALLOWED_ORIGINS` | sí | dominio del frontend en producción, ej. `https://tienditademarian.com` |
   | `CSRF_TRUSTED_ORIGINS` | recomendable | mismo dominio, con esquema `https://` |
   | `SECURE_HTTPS` | recomendable | `True` por default; ponerlo en `False` solo si el proxy delante todavía no tiene TLS (evita el bucle de redirección) |
   | `DEFAULT_FROM_EMAIL` / `EMAIL_*` | recomendable | remitente real y backend SMTP en vez de `console`/MailHog |
   | `DEBUG` | sí | `False` siempre en producción |

3. **Estáticos, migraciones y arranque** — ya están encadenados en el `CMD`
   del `Dockerfile`, pero si se despliega sin Docker (o hay que correrlos a
   mano una vez), son estos tres pasos en orden:

   ```bash
   python manage.py migrate --no-input
   python manage.py collectstatic --no-input
   gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60
   ```

4. **Healthcheck**: el orquestador (Docker, Kubernetes, el balanceador del
   proveedor) debe apuntar a `GET /healthz/` — es el mismo endpoint que usa
   el `HEALTHCHECK` del `Dockerfile` para decidir si el contenedor está listo.

### Frontend

```bash
cd frontend
npm ci
VITE_API_BASE_URL=https://api.tienditademarian.com npm run build
```

```powershell
cd frontend
npm ci
$env:VITE_API_BASE_URL = "https://api.tienditademarian.com"
npm run build
```

Las variables `VITE_*` quedan **embebidas en el bundle en tiempo de build**,
no se leen en runtime: hay que definir `VITE_API_BASE_URL` con la URL real de
la API de producción *antes* de correr `npm run build`, no después. El
resultado en `frontend/dist/` es estático: se sube a cualquier hosting de
archivos estáticos o CDN (Netlify, Vercel, S3+CloudFront, nginx propio, etc.).

---

## 7. Comandos útiles

| Acción | Comando |
|---|---|
| Arrancar backend (local) | `python manage.py runserver` |
| Arrancar frontend (local) | `npm run dev` |
| Arrancar todo (Docker) | `docker compose up --build` |
| Apagar Docker | `docker compose down` |
| Apagar Docker + borrar datos | `docker compose down -v` |
| Tests backend | `pytest` |
| Tests backend con cobertura | `pytest --cov` |
| Test de concurrencia (real, con Postgres) | `docker compose --profile test run --rm tests` |
| Humo del stack levantado | `bash scripts/smoke.sh` |
| **Reproducir el CI antes de pushear** | `bash scripts/verificar.sh` |
| Activar el hook que lo hace solo | `git config core.hooksPath .githooks` |
| Sembrar el catálogo demo (Docker) | `docker compose exec backend python manage.py cargar_productos` |
| Lint backend | `ruff check .` |
| Hardening de producción | `DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py check --deploy` |
| Tests frontend | `npm test` |
| Lint frontend | `npm run lint` |
| Build frontend | `npm run build` |
| Migraciones (local) | `python manage.py migrate` |
| Migraciones (Docker) | `docker compose run --rm backend python manage.py migrate` |
| Crear superusuario | `python manage.py createsuperuser` |
| Cargar catálogo demo | `python manage.py cargar_productos` |
| Shell de Django | `python manage.py shell` |
| Logs de un servicio (Docker) | `docker compose logs -f backend` |
| Reconstruir una imagen (Docker) | `docker compose build backend` (o `--no-cache` para forzar desde cero) |
| Entrar a un contenedor | `docker compose exec backend bash` |

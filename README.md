# 🧸 Tiendita de Marian

Monorepo del e-commerce **Tiendita de Marian**: una tienda en línea real con
catálogo, carrito, checkout transaccional, órdenes, pagos, envíos, descuentos,
reseñas y auditoría de eventos.

```
TienditaMarian/
├── backend/      API REST — Django 5.2 + DRF + JWT + PostgreSQL
├── frontend/     SPA — React 19 + Vite 7 + Tailwind 4
├── docker-compose.yml     Orquesta backend + frontend + PostgreSQL + MailHog
├── .github/workflows/     CI unificado (backend + frontend + humo del stack)
├── scripts/smoke.sh       humo del stack levantado (lo usa el CI y se corre en local)
├── scripts/verificar.sh   reproduce el CI en local, antes de pushear
├── .githooks/pre-push     lo ejecuta solo y cancela el push si falla
├── Jenkinsfile            Pipeline equivalente para Jenkins
├── pasos.md               Runbook: cómo levantarlo en local y en la web
└── docs/hosting-y-dominio.md   Dónde alojar web, base de datos y dominio
```

---

## Arranque rápido

**Con Docker (recomendado)** — levanta todo de una vez:

```bash
# genera un SECRET_KEY y ponlo en el entorno o en un .env de la raíz
docker compose up --build
docker compose exec backend python manage.py cargar_productos   # catálogo de demostración
```

- Tienda (frontend) → <http://localhost:5173>
- API → <http://localhost:8000/api/v1/>
- Documentación → <http://localhost:8000/api/schema/swagger-ui/>
- Correos de prueba (MailHog) → <http://localhost:8025>
- Salud del servicio → <http://localhost:8000/healthz/>
- PostgreSQL → `localhost:5433` (`POSTGRES_PORT` en el `.env` de la raíz)

> Dos trampas del `.env` de la raíz, ambas silenciosas: **el `SECRET_KEY` no puede
> llevar `$` sin escapar** (Compose lo interpola y la clave llega truncada), y **no
> es intercambiable con `backend/.env`** — el de la raíz usa el host `db`, que solo
> resuelve dentro de la red de Compose. Detalle en [`pasos.md`](pasos.md).

**Sin Docker** (venv + npm): el paso a paso completo, para Windows y Linux/Mac,
está en **[`pasos.md`](pasos.md)**.

---

## Los dos proyectos

| | Backend (`backend/`) | Frontend (`frontend/`) |
|---|---|---|
| Stack | Django 5.2 · DRF · SimpleJWT · PostgreSQL | React 19 · Vite 7 · Tailwind 4 |
| Arranque | `python manage.py runserver` | `npm run dev` |
| Tests | `pytest` (194, 93 % de cobertura) | `npm test` (25) |
| Lint | `ruff check .` | `npm run lint` |
| Detalle | [`backend/README.md`](backend/README.md) | `frontend/package.json` |

Sobre SQLite pasan 193 y se salta el de concurrencia del checkout, que necesita
PostgreSQL: `docker compose --profile test run --rm tests` corre los 194.

El backend documenta su arquitectura por capas (`core/`, `services`, `selectors`),
la decisión de diseño **ADR-001** (`GenericAPIView` + mixins sobre ViewSets) y el
flujo del checkout transaccional en su propio README.

---

## Arquitectura y despliegue

- **API versionada** en `/api/v1/` —y solo ahí: las rutas v0, que convivieron
  mientras el frontend migraba, ya se retiraron—, autenticación JWT (access corto
  + refresh con rotación y blacklist), autorización a nivel de objeto.
- **Frontend desacoplado en despliegue** pero en el mismo repo: se construye
  aparte (`npm run build` → `dist/`) y consume la API por `VITE_API_BASE_URL`. En
  local ambos corren juntos vía `docker-compose.yml`.
- **PostgreSQL** por `DATABASE_URL` (SQLite solo en tests).
- **Dónde alojarlo**: la recomendación concreta (frontend, API, Postgres, dominio,
  correo — con un stack de arranque casi $0) está en
  [`docs/hosting-y-dominio.md`](docs/hosting-y-dominio.md).

## CI

`.github/workflows/ci.yml` corre en cada push/PR, de lo más barato a lo más caro:

| Job | Qué verifica |
|---|---|
| `backend-test` | `ruff` + la suite sobre SQLite, con **90 %** de cobertura como condición de fallo |
| `backend-postgres` | la misma suite contra PostgreSQL real, donde `select_for_update` sí bloquea |
| `backend-deploy-check` | `check --deploy --fail-level WARNING` contra la config de producción |
| `frontend` | `eslint`, `vitest` y que el bundle **construya** |
| `docker-smoke` | construye las dos imágenes, **levanta el stack y lo usa** |

El último existe porque los otros cuatro llegaron a estar en verde sobre una
aplicación que no abría: hay fallos —rutas de estáticos sensibles a mayúsculas,
`/media/` sin servir con `DEBUG=False`, healthchecks que mienten— que solo
aparecen al construir el artefacto y arrancarlo. Corre
[`scripts/smoke.sh`](scripts/smoke.sh), que también se puede ejecutar en local
contra un `docker compose up` para reproducir el pipeline entero.

**Antes de pushear**: [`scripts/verificar.sh`](scripts/verificar.sh) reproduce en
local los cuatro primeros jobs, y el hook `.githooks/pre-push` lo ejecuta solo
(actívalo una vez con `git config core.hooksPath .githooks`). Existe porque hubo tres corridas en rojo por
warnings de drf-spectacular mientras `pytest` y `ruff` estaban en verde: el
único job que fallaba era el que no se ejecutaba a mano.

`Jenkinsfile` espeja el mismo pipeline.

---

Autor: **Nicolás Andrés Cano Leal** · Licencia MIT

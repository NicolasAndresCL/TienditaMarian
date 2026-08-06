# 🧸 Tiendita de Marian

Monorepo del e-commerce **Tiendita de Marian**: una tienda en línea real con
catálogo, carrito, checkout transaccional, órdenes, pagos, envíos, descuentos,
reseñas y auditoría de eventos.

```
TienditaMarian/
├── backend/      API REST — Django 5.2 + DRF + JWT + PostgreSQL
├── frontend/     SPA — React 19 + Vite 7 + Tailwind 4
├── docker-compose.yml     Orquesta backend + frontend + PostgreSQL + MailHog
├── .github/workflows/     CI unificado (backend + frontend)
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
```

- Tienda (frontend) → puerto publicado por el servicio `frontend`
- API → <http://localhost:8000/api/v1/>
- Documentación → <http://localhost:8000/api/schema/swagger-ui/>
- Correos de prueba (MailHog) → <http://localhost:8025>
- Salud del servicio → <http://localhost:8000/healthz/>

**Sin Docker** (venv + npm): el paso a paso completo, para Windows y Linux/Mac,
está en **[`pasos.md`](pasos.md)**.

---

## Los dos proyectos

| | Backend (`backend/`) | Frontend (`frontend/`) |
|---|---|---|
| Stack | Django 5.2 · DRF · SimpleJWT · PostgreSQL | React 19 · Vite 7 · Tailwind 4 |
| Arranque | `python manage.py runserver` | `npm run dev` |
| Tests | `pytest` (121) | `npm test` (12) |
| Lint | `ruff check .` | `npm run lint` |
| Detalle | [`backend/README.md`](backend/README.md) | `frontend/package.json` |

El backend documenta su arquitectura por capas (`core/`, `services`, `selectors`),
la decisión de diseño **ADR-001** (`GenericAPIView` + mixins sobre ViewSets) y el
flujo del checkout transaccional en su propio README.

---

## Arquitectura y despliegue

- **API versionada** en `/api/v1/`, autenticación JWT (access corto + refresh con
  rotación y blacklist), autorización a nivel de objeto.
- **Frontend desacoplado en despliegue** pero en el mismo repo: se construye
  aparte (`npm run build` → `dist/`) y consume la API por `VITE_API_BASE_URL`. En
  local ambos corren juntos vía `docker-compose.yml`.
- **PostgreSQL** por `DATABASE_URL` (SQLite solo en tests).
- **Dónde alojarlo**: la recomendación concreta (frontend, API, Postgres, dominio,
  correo — con un stack de arranque casi $0) está en
  [`docs/hosting-y-dominio.md`](docs/hosting-y-dominio.md).

## CI

`.github/workflows/ci.yml` corre en cada push/PR: lint + tests del backend
(SQLite y PostgreSQL), `check --deploy` de hardening, y lint + tests + build del
frontend. `Jenkinsfile` espeja el mismo pipeline.

---

Autor: **Nicolás Andrés Cano Leal** · Licencia MIT

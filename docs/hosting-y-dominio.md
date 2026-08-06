# Hosting y dominio — Tiendita de Marian

Recomendación de despliegue para la tienda online real de Marian (esposa de Nicolás).
Contexto: negocio real con **presupuesto acotado**, **tráfico bajo al inicio**, operado
desde **Chile**, con intención de crecer. El objetivo de esta guía es arrancar en
producción gastando lo mínimo posible (idealmente ~USD 0/mes) sin cerrarse la puerta a
escalar después.

> **Nota sobre precios:** todos los valores en USD/CLP de este documento son
> aproximados y cambian con el tiempo (planes, tipo de cambio, promociones). Verificar
> el precio vigente en el sitio del proveedor antes de pagar.

Stack del proyecto (para referencia rápida):

- **Backend:** Django + DRF, servido con `gunicorn config.wsgi:application`, healthcheck
  en `GET /healthz/`, `Dockerfile` multi-stage (build con `venv` + runtime slim, usuario
  no-root, `HEALTHCHECK` con `curl` a `/healthz/`).
- **Frontend:** React + Vite, SPA compilada a estático con `npm run build` (carpeta
  `dist/`); necesita `VITE_API_BASE_URL` definida **en tiempo de build** (queda embebida
  en el bundle, no es una variable de runtime).
- **Base de datos:** PostgreSQL, conexión vía `DATABASE_URL` con `dj-database-url` +
  `psycopg[binary]` (v3).
- **Config sensible al entorno:** `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`,
  `CSRF_TRUSTED_ORIGINS`, `SECURE_HTTPS` y variables `EMAIL_*` (en local usan MailHog
  vía SMTP en `localhost:1025`; en producción hace falta un SMTP real).

---

## 1. Frontend (SPA React/Vite)

| Proveedor | Tier gratis | Pros | Contras | Apto Chile |
|---|---|---|---|---|
| **Vercel** | Generoso: builds ilimitados, HTTPS, CDN global, dominios custom | Deploy automático desde GitHub (push a main = deploy), previews por PR, config casi cero para Vite, buena DX | Límites de ancho de banda/funciones en el free tier si el tráfico crece mucho; el enfoque "serverless functions" no aplica aquí (no lo necesitamos) | Sí — CDN con PoP en Sudamérica |
| **Netlify** | Similar a Vercel: build automático, HTTPS, previews de PR | Muy maduro, buen manejo de redirects/rewrites (útil para SPA routing), formularios gratis si se necesitaran | Límite de minutos de build/mes más ajustado que Vercel en el free tier | Sí — CDN global |
| **Cloudflare Pages** | Muy generoso: sin límite de ancho de banda en el free tier, builds ilimitados | Integrado con la red de Cloudflare (rápida en LatAm), HTTPS automático, si el dominio ya vive en Cloudflare la integración DNS es trivial | Ecosistema de "funciones" (Pages Functions) menos pulido que Vercel si algún día se necesitara SSR; comunidad/documentación un poco menor | Sí — buena presencia de PoPs en la región |

**Recomendación:** **Vercel** para el frontend. Es una SPA estática pura (sin SSR), así
que cualquiera de las tres opciones funciona técnicamente igual de bien, pero Vercel
tiene la mejor experiencia "conectar repo de GitHub → deploy automático en cada push"
con configuración prácticamente nula para un proyecto Vite estándar, y su tier gratis
sobra por años para el tráfico esperado. Alternativa igualmente válida: si el dominio
`.cl` termina gestionado en Cloudflare (ver sección 4), **Cloudflare Pages** es una
opción muy razonable para tener DNS y hosting del frontend en el mismo panel.

Detalle de build: configurar `VITE_API_BASE_URL=https://api.tienditademarian.cl` (o el
dominio elegido) como variable de entorno del proyecto en Vercel — se usa en build time,
así que hay que re-desplegar el frontend si cambia la URL de la API.

---

## 2. Backend (API Django + Gunicorn, Docker)

| Proveedor | Docker | Tier gratis/barato | Región cercana a Chile | Env vars | Healthcheck | Contras |
|---|---|---|---|---|---|---|
| **Render** | Sí, despliega directo desde `Dockerfile` | Free tier de Web Service existe pero **duerme tras inactividad** (cold start de ~30-60s); plan pago desde ~USD 7/mes para que no duerma | Oregon (us-west) u Ohio (us-east); no hay región en Sudamérica, pero Ohio da latencia razonable | UI simple para variables de entorno + secret files | Soporta `healthCheckPath` (`/healthz/`) nativamente | Free tier con cold start es molesto para una tienda real (primer pedido del día se cuelga) |
| **Railway** | Sí, `Dockerfile` o Nixpacks | Ya no tiene "free tier" permanente: da crédito de prueba (~USD 5) y luego es de pago por uso, desde ~USD 5/mes de plan Hobby | US West/East, Europa; sin región Sudamérica | Env vars por proyecto, muy simple | Soporta healthcheck HTTP configurable | El crédito gratis se acaba; hay que meter tarjeta pronto |
| **Fly.io** | Sí, nativo (`fly.toml` + Dockerfile) | Plan gratuito eliminado; ahora cobra por VM pero los montos para una VM pequeña (shared-cpu-1x, 256MB) rondan ~USD 2-5/mes | **Tiene región `scl` (Santiago, Chile)** y `gru` (São Paulo) — la única de las tres con presencia real en Chile | `fly secrets set` por CLI, cómodo para CI | Soporta `[[http_service.checks]]` apuntando a `/healthz/` | Curva de aprendizaje algo mayor (CLI propia, `fly.toml`); factura por uso puede sorprender si no se monitorea |
| **VPS (DigitalOcean, Hetzner)** | Total control, se corre el Dockerfile como se quiera (docker-compose) | No hay "gratis", pero Hetzner CX22 ronda ~€4/mes y DigitalOcean Droplet básico ~USD 6/mes | DigitalOcean tiene datacenter en São Paulo (`nyc`/`sfo` más lejos); Hetzner solo Europa/US | Manual (`.env` + systemd o compose), requiere disciplina propia | Manual (script/cron o compose healthcheck) | Hay que administrar SO, TLS (Caddy/Let's Encrypt), backups y seguridad a mano — mucho más trabajo operativo |

**Recomendación:** **Render** para arrancar. Su flujo "conectar repo → detecta el
`Dockerfile` → build y deploy automático en cada push" es el más simple de los tres, la
gestión de variables de entorno y el healthcheck (`/healthz/`) son de primera clase, y el
costo para salir del cold start (~USD 7/mes, plan Starter) es predecible y bajo. El
tráfico bajo inicial hace tolerable incluso el free tier con cold start los primeros
meses mientras se valida el negocio, y se puede subir al plan pago apenas empiece a
doler.

Alternativa a evaluar en paralelo: **Fly.io**, porque es el único de los tres con región
`scl` (Santiago) — la latencia hacia Chile sería la mejor posible (decenas de ms en vez
de ~150-200ms hacia EE.UU.). Si la latencia percibida en Render/Railway resulta molesta
para el equipo de Marian, migrar el backend a Fly.io con región `scl` es el siguiente
paso natural (el Dockerfile ya es portable entre los tres).

Si en algún momento Nicolás quiere control total (y ya sabe Docker/Terraform/K8s), un
**VPS en DigitalOcean con datacenter en São Paulo** es la opción de más control y menor
costo fijo, a cambio de administrar TLS, backups y seguridad manualmente — no recomendado
para el arranque, sí como paso de "cuando la tienda crezca" (ver sección final).

---

## 3. PostgreSQL gestionado

| Proveedor | Tier gratis | Backups | Límites free tier | `DATABASE_URL` |
|---|---|---|---|---|
| **Neon** | Sí, generoso (0.5 GB storage, autoscaling a 0 cuando no hay tráfico) | Point-in-time restore incluso en free tier (retención corta) | La DB "duerme" tras inactividad y despierta en el primer query (latencia extra en el primer request) | Da la cadena completa lista para copiar/pegar, compatible con `postgres://` |
| **Supabase** | Sí (500 MB DB, proyecto se pausa tras ~1 semana sin uso en free tier) | Backups diarios solo en planes pagos | Trae de regalo Auth/Storage/Realtime que este proyecto no necesita (Django ya maneja todo eso) | Cadena de conexión directa disponible en el panel |
| **Railway Postgres** | Ya no es gratis de forma permanente (mismo crédito de prueba que el resto de Railway) | Backups manuales/snapshot, no automáticos en Hobby | Atado al mismo crédito consumible que el backend | Variable `DATABASE_URL` inyectada automáticamente si backend y DB están en el mismo proyecto Railway |
| **Render Postgres** | Free tier existe pero **expira a los 30/90 días** y luego hay que migrar o pagar | Backups automáticos solo en planes pagos | Almacenamiento y conexiones limitadas en free | Se integra automáticamente si backend también está en Render (misma red interna) |

**Recomendación:** **Neon**. Tiene el tier gratis más sostenible en el tiempo (a
diferencia de Render Postgres, que expira, o Supabase, que pausa el proyecto), soporta
point-in-time restore incluso gratis, y da la `DATABASE_URL` lista para pegar
directamente. El único costo es un cold start ocasional (la DB "despierta" en ~500ms-1s
si estuvo inactiva), aceptable para el volumen de pedidos esperado al inicio.

Conexión: copiar la cadena que entrega Neon (formato
`postgresql://usuario:password@host/dbname?sslmode=require`) y pegarla tal cual en la
variable de entorno `DATABASE_URL` del servicio backend en Render (o el que se use). Como
el proyecto ya usa `dj-database-url` + `psycopg[binary]` v3 en `config/settings/prod.py`
(según `requirements/prod.txt`/`base.txt`), no hace falta ningún cambio de código: basta
con setear la variable de entorno. Importante: Neon exige SSL (`sslmode=require`), y
`dj-database-url` lo respeta si viene en la URL — no omitir ese query param.

Si más adelante el backend termina en Fly.io con región `scl`, vale la pena reevaluar
**Fly Postgres** (o una instancia gestionada más cercana) para minimizar la latencia
app↔DB, ya que hoy todas las opciones de la tabla viven en EE.UU./Europa.

---

## 4. Dominio

**Nombres sugeridos** (verificar disponibilidad real antes de registrar, esto es una
sugerencia de patrón, no una garantía de disponibilidad):

- `tienditademarian.cl` — primera opción: `.cl` da confianza local inmediata a clientes
  chilenos y es el ccTLD "natural" para una tienda que vende en Chile.
- `tienditademarian.com` — buena opción complementaria/alternativa si el `.cl` estuviera
  tomado o se quiere presencia internacional a futuro.
- Variantes de respaldo si los anteriores están ocupados: `tienditamarian.cl`,
  `tiendademarian.cl`, `tienditademarian.store`.

| Registrador | TLD | Costo aprox./año | Pros | Contras |
|---|---|---|---|---|
| **NIC Chile** (nic.cl, directo o vía reseller autorizado) | `.cl` | ~CLP 8.000–12.000/año (~USD 9-13) | Es el registro oficial chileno, requerido para `.cl`; da legitimidad local | El registro directo en NIC.cl es algo más burocrático que un registrador comercial; conviene usar un reseller con buen panel (p. ej. NIC.cl mismo tiene tienda propia) |
| **Cloudflare Registrar** | `.com` | Vende **al costo** (~USD 9-11/año, sin markup) | Precio más transparente del mercado, panel DNS de Cloudflare incluido gratis (proxy, analytics) | Solo se puede **transferir** dominios existentes o registrar TLDs soportados — no siempre es la vía más simple para un registro nuevo desde cero; no vende `.cl` |
| **Namecheap** | `.com` | ~USD 10-15/año (ojo con el precio de renovación, suele subir el 2do año) | Registro nuevo simple, promociones frecuentes el primer año, panel amigable | El precio de renovación es mayor al de bienvenida; no vende `.cl` |

**Recomendación:** registrar **`tienditademarian.cl`** en **NIC Chile** (directamente o
vía un reseller local) — es el dominio principal de cara a los clientes chilenos, con
costo bajo (~CLP 9.000-12.000/año) y máxima confianza local. Opcionalmente, registrar
también `tienditademarian.com` en **Cloudflare Registrar** (precio al costo, sin
sorpresas de renovación) y redirigirlo al `.cl`, para proteger la marca si se busca desde
fuera de Chile.

**DNS:** una vez registrado, apuntar así (usando Cloudflare como DNS, gratis, o el DNS
que ofrezca NIC Chile/el registrador):

- `tienditademarian.cl` (raíz) y `www.tienditademarian.cl` → registros que apunten al
  frontend en Vercel (Vercel entrega instrucciones exactas: normalmente un `CNAME` para
  `www` y un `A`/`ALIAS` para la raíz).
- `api.tienditademarian.cl` → `CNAME` hacia el dominio que entregue Render/Fly.io para el
  backend.

Con esto queda: SPA en la raíz, API en el subdominio `api.`. Hay que actualizar dos
variables acorde a este dominio final:

- `VITE_API_BASE_URL=https://api.tienditademarian.cl` en el proyecto de Vercel (rebuild
  del frontend tras el cambio).
- En el backend: `ALLOWED_HOSTS=api.tienditademarian.cl` y
  `CORS_ALLOWED_ORIGINS=https://tienditademarian.cl,https://www.tienditademarian.cl` (el
  backend ya lee `CORS_ALLOWED_ORIGINS` desde el entorno), más
  `CSRF_TRUSTED_ORIGINS=https://tienditademarian.cl` si se usan formularios con sesión/CSRF
  contra la API.

---

## 5. Correo transaccional

En local el proyecto usa **MailHog** (SMTP fake en `localhost:1025`, ver
`EMAIL_HOST`/`EMAIL_PORT` en `.env.example`) o el backend `console` de Django. En
producción se necesita un SMTP real para confirmaciones de compra, recuperación de
contraseña, etc.

| Proveedor | Tier gratis | Pros | Contras | Apto Chile |
|---|---|---|---|---|
| **Brevo (ex-Sendinblue)** | ~300 correos/día gratis, para siempre | Límite diario generoso para una tienda chica, panel en español, SMTP relay simple | El remitente debe verificar dominio (SPF/DKIM) para buena entregabilidad | Sí, sin restricciones |
| **Resend** | ~100 correos/día / 3.000/mes gratis | API y SMTP modernos, muy buena documentación, fácil de integrar | Tier gratis algo más chico que Brevo en volumen diario; producto más joven | Sí |
| **Mailgun** | Tier gratis reducido/discontinuado en muchos casos (revisar vigencia); planes desde ~USD 15/mes | Muy robusto, usado por empresas grandes, buena entregabilidad | Ya no es tan "gratis" como antes — conviene verificar el plan vigente antes de asumir costo cero | Sí |

**Recomendación:** **Brevo**. El límite de ~300 correos/día gratis "para siempre" (sin
tarjeta de crédito ni vencimiento) es más que suficiente para el volumen de pedidos
esperado al inicio, y el SMTP relay se cablea sin tocar código: solo hay que completar
las variables `EMAIL_*` que ya existen en el proyecto.

Configuración en producción (variables de entorno del backend):

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<usuario SMTP que da Brevo>
EMAIL_HOST_PASSWORD=<clave SMTP que da Brevo, no la contraseña de la cuenta>
DEFAULT_FROM_EMAIL=no-reply@tienditademarian.cl
CONTACTO_EMAIL=contacto@tienditademarian.cl
```

Para que Brevo entregue con buena reputación (no caer en spam), conviene agregar los
registros SPF/DKIM que Brevo entrega al dominio `tienditademarian.cl` en el panel DNS
(Cloudflare o el que se use).

---

## Stack recomendado de arranque (casi $0)

```
                         Cliente (navegador)
                                │
                    tienditademarian.cl (DNS)
                     /                    \
                    /                      \
        tienditademarian.cl        api.tienditademarian.cl
                │                              │
                ▼                              ▼
        ┌───────────────┐            ┌──────────────────┐
        │     Vercel     │  HTTPS     │      Render       │
        │  React + Vite  │──────────▶ │ Django + Gunicorn  │
        │   (dist/ CDN)  │  fetch()   │  (Docker, /healthz/)│
        └───────────────┘            └─────────┬─────────┘
                                                 │ DATABASE_URL (SSL)
                                                 ▼
                                          ┌─────────────┐
                                          │     Neon      │
                                          │  PostgreSQL   │
                                          └─────────────┘

        Confirmaciones de compra ──▶ SMTP Brevo (smtp-relay.brevo.com)
```

| Componente | Proveedor | Costo aprox. |
|---|---|---|
| Frontend | Vercel (Hobby) | ~USD 0/mes |
| Backend | Render (Starter, para evitar cold start) | ~USD 7/mes (o USD 0 si se tolera el sleep del free tier al inicio) |
| Base de datos | Neon (Free) | ~USD 0/mes |
| Dominio `.cl` | NIC Chile | ~CLP 9.000-12.000/año (~USD 10-13/año ≈ USD 1/mes) |
| Correo transaccional | Brevo (Free) | ~USD 0/mes |
| **Total estimado** | | **~USD 1-8/mes** (~USD 12-100/año), según si se paga o no el plan Starter de Render |

Es perfectamente viable arrancar en **~USD 0-1/mes** (solo el dominio) tolerando el cold
start de Render mientras el volumen de pedidos es bajo, y subir a ~USD 7-8/mes en cuanto
el cold start empiece a afectar la experiencia de compra real.

---

## Cuando la tienda crezca

Camino de escalado, coherente con que Nicolás ya maneja Docker/Terraform/Kubernetes:

1. **Backend:** migrar de Render a **Fly.io con región `scl` (Santiago)** o a un
   **VPS/cluster propio** (DigitalOcean/Hetzner) si se necesita más control sobre
   recursos, colas de trabajo (Celery) o múltiples réplicas. El Dockerfile multi-stage
   actual ya es portable a cualquiera de estos destinos sin cambios.
2. **Base de datos:** subir de Neon Free a un **plan de pago** (Neon Pro, o
   directamente **RDS/Cloud SQL/instancia gestionada en la misma nube que el backend**)
   para eliminar el cold start, tener backups con retención larga y más IOPS. Si el
   backend termina en un VPS propio, evaluar Postgres gestionado en la misma región para
   bajar la latencia app↔DB a <5ms.
3. **CDN:** si el catálogo crece con muchas imágenes de producto, poner **Cloudflare
   delante del backend** (proxy naranja) para cachear estáticos/medios y absorber picos
   de tráfico (ej. promociones, Cyber Monday), además de WAF básico gratis.
4. **Dominio propio ya consolidado:** una vez validado el negocio, asegurar
   `tienditademarian.com` además del `.cl` (si no se hizo antes) y considerar
   `correo@tienditademarian.cl` con Google Workspace o Zoho Mail para correo
   institucional (no solo transaccional).
5. **Observabilidad:** sumar **Sentry** (error tracking, tier gratis generoso) para el
   backend y frontend, y métricas básicas de infraestructura (Grafana Cloud free tier o
   los dashboards nativos de Fly.io/DigitalOcean) antes de que el volumen de pedidos haga
   que un error silencioso cueste ventas reales.
6. **Infraestructura como código:** si se migra a VPS o a un proveedor con múltiples
   servicios (DB, cache, workers), formalizar el despliegue con **Terraform** (ya lo
   maneja Nicolás) en vez de clicks manuales en paneles — facilita reproducir el entorno
   y hacer rollback.
7. **Kubernetes:** solo si el negocio realmente escala a múltiples servicios/equipos
   trabajando en paralelo (poco probable para esta tienda en el corto/mediano plazo); para
   un monolito Django + SPA con tráfico moderado, un VPS bien configurado o Fly.io siguen
   siendo más simples y baratos que mantener un cluster K8s.

---

## Consideraciones de latencia y configuración

- **Latencia hacia Chile:** ninguna de las opciones "gratis" recomendadas (Vercel,
  Render, Neon) tiene datacenter en Chile. Vercel y Neon mitigan esto con CDN/edge
  global; Render corre en EE.UU. (Oregon/Ohio), lo que agrega ~150-200ms de latencia a
  cada request de la API desde Chile — aceptable para una tienda con tráfico bajo, pero
  el primer candidato a mejorar (migrando el backend a **Fly.io región `scl`**) si la
  UX empieza a sentirse lenta.
- **CORS:** el backend ya lee `CORS_ALLOWED_ORIGINS` desde el entorno — en producción
  debe listar **exactamente** los orígenes del frontend servidos por HTTPS
  (`https://tienditademarian.cl,https://www.tienditademarian.cl`), sin comodines ni
  `http://` de desarrollo mezclado.
- **ALLOWED_HOSTS:** debe incluir el host real del backend
  (`api.tienditademarian.cl`, y el host que asigne Render/Fly.io por defecto, ej.
  `tiendita-marian.onrender.com`, útil para probar antes de que el DNS propague).
- **HTTPS:** todos los proveedores recomendados (Vercel, Render, Fly.io, Neon, Cloudflare)
  dan HTTPS automático vía Let's Encrypt sin configuración adicional; activar
  `SECURE_HTTPS=True` y `CSRF_TRUSTED_ORIGINS` en `config/settings/prod.py` una vez el
  dominio final esté conectado.

# Imagen de producción del frontend: multi-stage y sin root (estándar del repo).
#
# Stage 1 (build): Node compila el bundle con Vite → dist/.
# Stage 2 (runtime): nginx sirve esos estáticos. La imagen final NO lleva Node ni
# node_modules (cientos de MB): solo nginx + los archivos ya compilados.

# ---------------------------------------------------------------- build
FROM node:20-alpine AS build

WORKDIR /app

# Se copian solo los manifiestos antes que el resto del código para aprovechar la
# cache de capas de Docker: si el código cambia pero las dependencias no, `npm ci`
# no se vuelve a ejecutar.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# VITE_API_BASE_URL se inyecta como BUILD ARG, no como env de runtime, porque
# Vite EMBEBE las variables VITE_* dentro del bundle en tiempo de compilación:
# una vez construido dist/, la URL ya está "horneada" en el JS y no se puede
# cambiar al arrancar el contenedor. Por eso en prod se construye la imagen
# apuntando al dominio real de la API (build arg distinto), no con una env var.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

# ---------------------------------------------------------------- runtime
FROM nginx:alpine AS runtime

# Configuración propia (incluye pid y rutas temporales en ubicaciones escribibles
# por un usuario sin privilegios). Reemplaza la config principal de la imagen.
COPY nginx.conf /etc/nginx/nginx.conf

# Solo los artefactos ya compilados: la SPA estática.
COPY --from=build /app/dist /usr/share/nginx/html

# El proceso no debe correr como root. El usuario `nginx` ya existe en la imagen,
# pero por defecto no puede escribir el pid en /var/run ni los temporales en
# /var/cache (son de root); se reubican a /tmp/nginx y se ajusta la propiedad.
RUN mkdir -p /tmp/nginx \
    && chown -R nginx:nginx /tmp/nginx /usr/share/nginx/html

USER nginx

EXPOSE 80

# En Docker un proceso no-root puede escuchar en el puerto 80 porque el daemon
# fija net.ipv4.ip_unprivileged_port_start=0 por defecto en el contenedor.
# 127.0.0.1 y no `localhost`: dentro del contenedor, `localhost` resuelve primero
# a ::1, y nginx con `listen 80;` solo abre el socket IPv4. El wget de BusyBox no
# reintenta con IPv4 —curl sí, por eso el healthcheck del backend nunca dio
# problemas—, así que este daba "Connection refused" en cada corrida y el
# contenedor vivía marcado `unhealthy` mientras servía la SPA perfectamente. Con
# `depends_on: condition: service_healthy` delante, eso bloquea un despliegue.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

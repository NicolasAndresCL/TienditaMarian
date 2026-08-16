/**
 * API simulada para los tests del flujo.
 *
 * MSW intercepta a nivel de red, no mockeando `axios`: los tests ejercitan el
 * cliente HTTP de verdad —sus interceptores, el token CSRF, `withCredentials`—
 * en vez de un doble que podría desviarse de él sin que nadie se entere.
 */
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

// Se deriva de la MISMA variable que usa el cliente HTTP real, no de una copia
// escrita a mano: si las dos divergen, MSW deja de reconocer las peticiones y
// estas salen a la red de verdad, con un error de "sin conexión" que no dice
// nada de la causa. Su valor para los tests lo fija `vite.config.js`.
const API = `${import.meta.env.VITE_API_BASE_URL}/api/v1`;

export const PRODUCTOS = [
  {
    id: 1,
    nombre: 'Bugs Bunny',
    descripcion: 'Peluche clásico de Bugs Bunny.',
    precio: '6000.00',
    stock: 2,
    image: null,
  },
  {
    id: 2,
    nombre: 'Randall',
    descripcion: 'Peluche de Randall, de Monsters Inc.',
    precio: '7000.00',
    stock: 0,
    image: null,
  },
];

/** Cuerpo de error con la forma que garantiza el backend en TODA la API. */
export function errorDeApi(codigo, mensaje, detalle = {}, status = 400) {
  return HttpResponse.json({ error: { codigo, mensaje, detalle } }, { status });
}

export const handlers = [
  http.get(`${API}/productos/`, () =>
    HttpResponse.json({ count: PRODUCTOS.length, next: null, previous: null, results: PRODUCTOS }),
  ),
  http.get(`${API}/productos/:id/`, ({ params }) => {
    const producto = PRODUCTOS.find((p) => String(p.id) === String(params.id));
    return producto
      ? HttpResponse.json(producto)
      : errorDeApi('producto_no_encontrado', 'El producto no existe.', {}, 404);
  }),
  // Sin sesión por defecto: cada test que necesite una la declara.
  http.get(`${API}/auth/me/`, () => new HttpResponse(null, { status: 401 })),
  http.post(`${API}/auth/token/refresh/`, () => new HttpResponse(null, { status: 401 })),
  http.get(`${API}/carrito/`, () => new HttpResponse(null, { status: 401 })),
];

export const servidor = setupServer(...handlers);
export { http, HttpResponse, API };

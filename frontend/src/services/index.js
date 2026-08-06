/**
 * Servicios de la API.
 *
 * Antes había tres archivos con la misma constante `API_BASE_URL` repetida, la
 * cabecera `Authorization` copiada en cada función y el token pasándose como
 * parámetro. Además, `carritoService.js` y `ordenesService.js` (81 líneas) eran
 * CÓDIGO MUERTO: nadie los importaba. El botón "agregar al carrito" era un
 * `alert('Producto agregado (simulado)')`.
 *
 * Ahora todo pasa por el cliente único, que ya inyecta el token y renueva la
 * sesión cuando expira.
 */
import api, { apiSinAuth } from '../api/client';
import { guardarTokens, borrarTokens, leerTokens } from '../api/tokens';

// ---------------------------------------------------------------- auth

export async function login(username, password) {
  const { data } = await apiSinAuth.post('/auth/token/', { username, password });
  // El refresh se guarda: antes se descartaba y la sesión moría en silencio.
  guardarTokens({ access: data.access, refresh: data.refresh });
  return data;
}

export async function registrar({ username, email, password, passwordConfirm }) {
  const { data } = await apiSinAuth.post('/auth/register/', {
    username,
    email,
    password,
    password_confirm: passwordConfirm,
  });
  // El registro ya deja la sesión iniciada: el backend devuelve los tokens.
  guardarTokens(data.token);
  return data;
}

export async function logout() {
  const { refresh } = leerTokens();
  try {
    // Invalida el refresh en el servidor (blacklist). Sin esto, un token robado
    // seguiría siendo válido durante días aunque el usuario cerrara sesión.
    if (refresh) await api.post('/auth/logout/', { refresh });
  } finally {
    // Pase lo que pase en el servidor, la sesión local se cierra.
    borrarTokens();
  }
}

// ---------------------------------------------------------------- productos

export async function obtenerProductos() {
  const { data } = await apiSinAuth.get('/productos/');
  // La API pagina: devuelve { count, next, previous, results }. El código
  // anterior hacía `setProductos(response.data)` y luego `productos.map(...)`
  // sobre un objeto, no sobre un array.
  return data.results;
}

export async function obtenerProducto(id) {
  const { data } = await apiSinAuth.get(`/productos/${id}/`);
  return data;
}

// ---------------------------------------------------------------- carrito

export async function obtenerCarrito() {
  const { data } = await api.get('/carrito/');
  return data;
}

export async function agregarAlCarrito(productoId, cantidad = 1) {
  const { data } = await api.post('/carrito/items/', {
    producto_id: productoId,
    cantidad,
  });
  return data;
}

export async function actualizarCantidad(productoId, cantidad) {
  const { data } = await api.patch('/carrito/items/cantidad/', {
    producto_id: productoId,
    cantidad,
  });
  return data;
}

export async function quitarDelCarrito(productoId) {
  await api.delete('/carrito/items/quitar/', { data: { producto_id: productoId } });
}

export async function vaciarCarrito() {
  await api.delete('/carrito/vaciar/');
}

export async function checkout(cupon) {
  const { data } = await api.post('/checkout/', cupon ? { cupon } : {});
  return data;
}

// ---------------------------------------------------------------- órdenes

export async function obtenerOrdenes() {
  const { data } = await api.get('/ordenes/');
  return data.results;
}

export async function obtenerOrden(id) {
  const { data } = await api.get(`/ordenes/${id}/`);
  return data;
}

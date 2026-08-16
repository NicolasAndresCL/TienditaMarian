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

// ---------------------------------------------------------------- auth
//
// Ninguna de estas funciones toca el token: la sesión vive en cookies httpOnly
// que pone y quita el backend. Antes había que guardarlo, pasarlo y borrarlo a
// mano, y el `refresh` sencillamente se descartaba.

export async function login(username, password) {
  const { data } = await apiSinAuth.post('/auth/token/', { username, password });
  return data;
}

export async function registrar({ username, email, password, passwordConfirm }) {
  const { data } = await apiSinAuth.post('/auth/register/', {
    username,
    email,
    password,
    password_confirm: passwordConfirm,
  });
  // El registro ya deja la sesión iniciada: el backend manda las cookies.
  return data;
}

export async function logout() {
  // Invalida el refresh en el servidor (blacklist) y borra las cookies. Sin
  // esto, un token robado seguiría siendo válido durante días aunque la usuaria
  // hubiera cerrado sesión.
  await api.post('/auth/logout/', {});
}

/** Quién es la sesión actual, o `null` si no hay ninguna.
 *
 * El frontend ya no puede mirar el token para saberlo —es httpOnly—, así que lo
 * pregunta. De paso resuelve algo que antes fallaba: al recargar la página se
 * sabía que había sesión pero no de quién era, y el nombre desaparecía de la
 * barra hasta el siguiente login.
 */
export async function obtenerSesion() {
  // Va por `apiSinAuth` a propósito: con el cliente normal, un 401 aquí
  // dispararía el interceptor de renovación y, al fallar, el evento
  // `sesion-expirada`. Es decir, a un visitante que NUNCA inició sesión se le
  // mostraría "Tu sesión expiró" nada más abrir la tienda.
  try {
    const { data } = await apiSinAuth.get('/auth/me/');
    return data;
  } catch {
    // Puede que solo haya caducado el access (dura 15 minutos) y el refresh
    // siga vivo en su cookie. Se intenta una vez, explícitamente.
    try {
      await apiSinAuth.post('/auth/token/refresh/', {});
      const { data } = await apiSinAuth.get('/auth/me/');
      return data;
    } catch {
      return null;
    }
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

/** Cobra una orden y devuelve la orden ya pagada.
 *
 * El backend hace el cobro completo: bloquea la fila, registra el pago, marca la
 * orden y avisa por correo. Es idempotente — pagar dos veces devuelve un 409 con
 * el código `orden_ya_pagada`, nunca un segundo cobro.
 */
export async function pagarOrden(id) {
  const { data } = await api.post(`/ordenes/${id}/pagar/`, {});
  return data;
}

/** Reserva la transacción en Webpay y devuelve a dónde hay que ir a pagar.
 *
 * No completa el pago: devuelve `{ url, token }`. La clienta tiene que llegar a
 * esa URL **por POST**, con el token en un campo `token_ws` — Transbank no
 * acepta una redirección normal. Lo hace `redirigirAWebpay`.
 */
export async function iniciarPagoWebpay(id) {
  const { data } = await api.post(`/ordenes/${id}/pagar/webpay/`, {});
  return data;
}

/** Envía el navegador a Transbank con el token, por POST. */
export function redirigirAWebpay({ url, token }) {
  const formulario = document.createElement('form');
  formulario.method = 'POST';
  formulario.action = url;

  const campo = document.createElement('input');
  campo.type = 'hidden';
  campo.name = 'token_ws';
  campo.value = token;

  formulario.appendChild(campo);
  document.body.appendChild(formulario);
  formulario.submit();
}

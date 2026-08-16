import axios from 'axios';
import { leerTokenCsrf } from './tokens';

/**
 * Cliente HTTP único de la aplicación.
 *
 * Antes no existía: se usaba `axios` pelado, la baseURL se repetía en cinco
 * archivos y la cabecera `Authorization` estaba copiada a mano ocho veces, con
 * el token viajando como parámetro de función. No había ni un interceptor.
 *
 * Lo más grave era la sesión: el backend devuelve { access, refresh } y el
 * `refresh` se **descartaba**. Cuando el access expiraba (15 minutos), la app
 * quedaba en un estado roto silencioso: no reintentaba, no deslogueaba, no
 * avisaba.
 *
 * Hoy la sesión ya no la maneja este archivo en absoluto: vive en cookies
 * `HttpOnly` que pone el backend y que el navegador adjunta sola. Aquí solo
 * queda `withCredentials` —para que esas cookies viajen aunque la API esté en
 * otro puerto— y el token CSRF, que es el precio de que el navegador autentique
 * por su cuenta.
 */
const configuracionComun = {
  baseURL: `${import.meta.env.VITE_API_BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  // Sin esto el navegador NO manda las cookies a otro origen (:5173 → :8000) ni
  // guarda las que el backend devuelve: la sesión no existiría.
  withCredentials: true,
};

const api = axios.create(configuracionComun);

/** Cliente sin interceptores, para renovar el token sin caer en un bucle. */
const apiSinAuth = axios.create(configuracionComun);

// Petición: el token CSRF va en cada llamada que escribe. El de sesión ya no se
// toca — lo pone el navegador y este código ni siquiera puede verlo.
const metodosQueEscriben = ['post', 'put', 'patch', 'delete'];

function agregarCsrf(config) {
  if (metodosQueEscriben.includes(config.method)) {
    const token = leerTokenCsrf();
    if (token) {
      config.headers['X-CSRFToken'] = token;
    }
  }
  return config;
}

api.interceptors.request.use(agregarCsrf);
apiSinAuth.interceptors.request.use(agregarCsrf);

// `apiSinAuth` no renueva la sesión —para eso existe, para no caer en un bucle—
// pero sus errores tienen que llegar traducidos igual que los del otro cliente.
// Sin esto, el catálogo y el detalle de producto (que son públicos y van por
// aquí) mostraban "Ocurrió un error." genérico mientras el backend estaba
// diciendo "El producto no existe": justo lo que el cliente único vino a
// arreglar, pero solo para la mitad de las llamadas.
apiSinAuth.interceptors.response.use(
  (respuesta) => respuesta,
  (error) => Promise.reject(normalizarError(error)),
);

// Si varias peticiones reciben 401 a la vez, solo se renueva el token UNA vez y
// las demás esperan a esa misma promesa. Sin esto, cinco llamadas simultáneas
// dispararían cinco refresh y, con la rotación activada en el backend, cuatro
// quedarían inválidos.
let renovacionEnCurso = null;

async function renovarAccess() {
  // El refresh no se manda: viaja en su propia cookie httpOnly, que este código
  // no puede leer. El backend la lee y reescribe ambas cookies con los tokens
  // nuevos (rotación).
  await apiSinAuth.post('/auth/token/refresh/', {});
}

// Respuesta: ante un 401, renueva la sesión y reintenta la petición original.
api.interceptors.response.use(
  (respuesta) => respuesta,
  async (error) => {
    const original = error.config;
    const esNoAutorizado = error.response?.status === 401;

    // `_reintentado` evita el bucle infinito: si el reintento vuelve a dar 401,
    // se acepta la derrota y se cierra la sesión.
    if (!esNoAutorizado || original._reintentado) {
      return Promise.reject(normalizarError(error));
    }

    original._reintentado = true;

    try {
      renovacionEnCurso = renovacionEnCurso ?? renovarAccess();
      await renovacionEnCurso;
      renovacionEnCurso = null;

      // No hay que tocar cabeceras: la cookie nueva ya está puesta y el
      // navegador la adjunta en el reintento.
      return api(original);
    } catch (fallo) {
      renovacionEnCurso = null;
      // Avisa a la app para que redirija al login, en vez de dejar la interfaz
      // colgada sin explicación.
      window.dispatchEvent(new CustomEvent('sesion-expirada'));
      return Promise.reject(normalizarError(fallo));
    }
  },
);

/**
 * Traduce el error del backend a algo que la interfaz pueda mostrar.
 *
 * El backend responde siempre con la misma forma:
 *   { error: { codigo, mensaje, detalle } }
 * Antes se hacía `catch { setError('No se pudieron cargar los productos') }`
 * —sin capturar la excepción siquiera—, así que un 500, un CORS y un 401 se
 * mostraban todos igual, y el mensaje real del backend se tiraba a la basura.
 */
export function normalizarError(error) {
  const cuerpo = error.response?.data?.error;

  if (cuerpo) {
    return {
      codigo: cuerpo.codigo,
      mensaje: cuerpo.mensaje,
      detalle: cuerpo.detalle ?? {},
      status: error.response.status,
    };
  }

  if (error.response) {
    return {
      codigo: 'error_servidor',
      mensaje: 'Algo falló en el servidor. Inténtalo de nuevo en un momento.',
      detalle: {},
      status: error.response.status,
    };
  }

  return {
    codigo: 'sin_conexion',
    mensaje: 'No pudimos conectar con la tienda. Revisa tu conexión.',
    detalle: {},
    status: 0,
  };
}

export default api;
export { apiSinAuth };

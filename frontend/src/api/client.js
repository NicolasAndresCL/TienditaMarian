import axios from 'axios';
import { leerTokens, guardarTokens, borrarTokens } from './tokens';

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
 * avisaba. Simplemente dejaba de funcionar.
 */
const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

/** Cliente sin interceptores, para renovar el token sin caer en un bucle. */
const apiSinAuth = axios.create({
  baseURL: `${import.meta.env.VITE_API_BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

// Petición: inyecta el Bearer en cada llamada.
api.interceptors.request.use((config) => {
  const { access } = leerTokens();
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

// Si varias peticiones reciben 401 a la vez, solo se renueva el token UNA vez y
// las demás esperan a esa misma promesa. Sin esto, cinco llamadas simultáneas
// dispararían cinco refresh y, con la rotación activada en el backend, cuatro
// quedarían inválidos.
let renovacionEnCurso = null;

async function renovarAccess() {
  const { refresh } = leerTokens();
  if (!refresh) throw new Error('sin refresh token');

  const { data } = await apiSinAuth.post('/auth/token/refresh/', { refresh });
  // El backend rota el refresh: hay que guardar el nuevo, si viene.
  guardarTokens({ access: data.access, refresh: data.refresh ?? refresh });
  return data.access;
}

// Respuesta: ante un 401, renueva el token y reintenta la petición original.
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
      const nuevoAccess = await renovacionEnCurso;
      renovacionEnCurso = null;

      original.headers.Authorization = `Bearer ${nuevoAccess}`;
      return api(original);
    } catch (fallo) {
      renovacionEnCurso = null;
      borrarTokens();
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

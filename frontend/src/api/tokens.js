/**
 * Lectura del token CSRF.
 *
 * Este archivo guardaba los JWT en `localStorage`. Ya no: la sesión vive en
 * cookies `HttpOnly` que el navegador manda sola y que **ningún JavaScript
 * puede leer**, ni el nuestro ni el que inyecte un XSS. Por eso desaparecieron
 * `leerTokens`, `guardarTokens` y `borrarTokens`: no hay nada que guardar.
 *
 * A cambio, como el navegador adjunta la sesión por su cuenta, un sitio ajeno
 * podría provocar peticiones a la API en nombre de la usuaria. La defensa es el
 * token CSRF: el backend lo deja en una cookie legible (a propósito) y aquí se
 * lee para reenviarlo en la cabecera `X-CSRFToken`. Un sitio ajeno no puede
 * leer esa cookie —la política de mismo origen se lo impide— así que no puede
 * construir la cabecera.
 */
const COOKIE_CSRF = 'csrftoken';

export function leerTokenCsrf() {
  const encontrada = document.cookie
    .split('; ')
    .find((cookie) => cookie.startsWith(`${COOKIE_CSRF}=`));

  return encontrada ? decodeURIComponent(encontrada.split('=')[1]) : null;
}

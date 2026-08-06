/**
 * Único lugar que toca el almacenamiento de la sesión.
 *
 * Antes el token lo guardaba el componente `Login` con un `localStorage.setItem`
 * suelto, y además lo subía por un callback: dos fuentes de verdad para la misma
 * sesión. El `refresh` ni se guardaba, y no existía ningún `logout`
 * (`removeItem` no aparecía en el proyecto).
 *
 * Nota de seguridad: `localStorage` es accesible desde JavaScript, así que un XSS
 * puede robar el token. Lo correcto sería una cookie httpOnly, pero eso exige que
 * el backend fije la cookie y cambiar el flujo de JWT entero. Mientras tanto, la
 * mitigación real es que el access dura 15 minutos y el logout invalida el
 * refresh en el servidor (blacklist).
 */
const CLAVE_ACCESS = 'tiendita.access';
const CLAVE_REFRESH = 'tiendita.refresh';

export function leerTokens() {
  return {
    access: localStorage.getItem(CLAVE_ACCESS),
    refresh: localStorage.getItem(CLAVE_REFRESH),
  };
}

export function guardarTokens({ access, refresh }) {
  if (access) localStorage.setItem(CLAVE_ACCESS, access);
  if (refresh) localStorage.setItem(CLAVE_REFRESH, refresh);
}

export function borrarTokens() {
  localStorage.removeItem(CLAVE_ACCESS);
  localStorage.removeItem(CLAVE_REFRESH);
}

export function haySesion() {
  return Boolean(localStorage.getItem(CLAVE_ACCESS));
}

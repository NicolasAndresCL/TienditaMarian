import { useState, useEffect, useCallback } from 'react';
import * as servicios from '../services';
import { AuthContext } from './contextos';

/**
 * Estado de sesión compartido.
 *
 * Antes el token vivía en un `useState` de App y se prop-drilleaba hasta cada
 * ProductoCard junto con un callback `onRequireLogin`. Con un nivel más de
 * anidamiento eso se vuelve inmanejable.
 *
 * Con la sesión en cookies httpOnly este componente ya no puede inspeccionar el
 * token para saber si hay sesión: se lo pregunta al backend (`/auth/me/`) al
 * montar. Eso arregla de paso un detalle que antes fallaba — al recargar la
 * página se sabía que había sesión pero no de quién era, así que el nombre
 * desaparecía de la barra hasta el siguiente login.
 */
export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [error, setError] = useState(null);
  // `null` = todavía no sabemos. Importa para no mandar al login a alguien que
  // sí tiene sesión solo porque la comprobación aún no volvió.
  const [autenticado, setAutenticado] = useState(null);

  useEffect(() => {
    let vigente = true;

    servicios.obtenerSesion().then((sesion) => {
      if (!vigente) return;
      setUsuario(sesion);
      setAutenticado(Boolean(sesion));
    });

    return () => {
      vigente = false;
    };
  }, []);

  // El cliente HTTP avisa cuando la sesión ya no sirve. Antes, al expirar, la
  // app se quedaba muerta sin decir nada.
  useEffect(() => {
    const alExpirar = () => {
      setAutenticado(false);
      setUsuario(null);
      setError({ codigo: 'sesion_expirada', mensaje: 'Tu sesión expiró. Vuelve a entrar.' });
    };

    window.addEventListener('sesion-expirada', alExpirar);
    return () => window.removeEventListener('sesion-expirada', alExpirar);
  }, []);

  const entrar = useCallback(async (username, password) => {
    setError(null);
    try {
      await servicios.login(username, password);
      setUsuario(await servicios.obtenerSesion());
      setAutenticado(true);
      return true;
    } catch (fallo) {
      // Se muestra el mensaje real del backend. El código anterior decía
      // "Usuario o contraseña incorrectos" incluso ante un 500 o un fallo de red.
      setError(fallo);
      return false;
    }
  }, []);

  const registrarse = useCallback(async (datos) => {
    setError(null);
    try {
      const respuesta = await servicios.registrar(datos);
      setUsuario(respuesta.usuario);
      setAutenticado(true);
      return true;
    } catch (fallo) {
      setError(fallo);
      return false;
    }
  }, []);

  const salir = useCallback(async () => {
    try {
      await servicios.logout();
    } catch {
      // Las cookies las borra el servidor; si la petición falla, la sesión local
      // se cierra igual y el token caduca solo.
    } finally {
      setAutenticado(false);
      setUsuario(null);
    }
  }, []);

  const valor = {
    autenticado,
    usuario,
    error,
    entrar,
    registrarse,
    salir,
    limpiarError: () => setError(null),
  };

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

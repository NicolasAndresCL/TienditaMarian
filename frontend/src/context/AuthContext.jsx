import { useState, useEffect, useCallback } from 'react';
import * as servicios from '../services';
import { haySesion, borrarTokens } from '../api/tokens';
import { AuthContext } from './contextos';

/**
 * Estado de sesión compartido.
 *
 * Antes el token vivía en un `useState` de App y se prop-drilleaba hasta cada
 * ProductoCard junto con un callback `onRequireLogin`. Con un nivel más de
 * anidamiento eso se vuelve inmanejable.
 */
export function AuthProvider({ children }) {
  const [autenticado, setAutenticado] = useState(haySesion);
  const [usuario, setUsuario] = useState(null);
  const [error, setError] = useState(null);

  // El cliente HTTP avisa cuando el refresh token ya no sirve. Antes, al expirar
  // la sesión la app se quedaba muerta sin decir nada.
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
      setAutenticado(true);
      setUsuario({ username });
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
      setAutenticado(true);
      setUsuario(respuesta.usuario);
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
      borrarTokens();
    } finally {
      setAutenticado(false);
      setUsuario(null);
    }
  }, []);

  const valor = { autenticado, usuario, error, entrar, registrarse, salir, limpiarError: () => setError(null) };

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}


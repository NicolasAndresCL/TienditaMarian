import { createContext, useContext } from 'react';

/**
 * Los contextos y sus hooks viven aquí, separados de los componentes Provider.
 *
 * No es un capricho: Fast Refresh solo funciona si un archivo exporta
 * únicamente componentes. Mezclar el Provider con el hook `useAuth` en el mismo
 * archivo rompe el refresco en caliente (y eslint-plugin-react-refresh lo marca).
 */

export const AuthContext = createContext(null);
export const CarritoContext = createContext(null);

export function useAuth() {
  const contexto = useContext(AuthContext);
  if (!contexto) {
    throw new Error('useAuth debe usarse dentro de un <AuthProvider>');
  }
  return contexto;
}

export function useCarrito() {
  const contexto = useContext(CarritoContext);
  if (!contexto) {
    throw new Error('useCarrito debe usarse dentro de un <CarritoProvider>');
  }
  return contexto;
}

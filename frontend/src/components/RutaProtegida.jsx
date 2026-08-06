import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/contextos';

/**
 * Rutas que exigen sesión.
 *
 * No existían: la app "navegaba" con banderas booleanas (`showLogin`,
 * `showRegister`) y un early-return que reemplazaba la pantalla entera. No había
 * URLs, ni enlaces compartibles, ni botón atrás.
 */
export default function RutaProtegida({ children }) {
  const { autenticado } = useAuth();
  const ubicacion = useLocation();

  if (!autenticado) {
    // Se guarda de dónde venía para devolverlo ahí después de entrar.
    return <Navigate to="/login" state={{ desde: ubicacion.pathname }} replace />;
  }

  return children;
}

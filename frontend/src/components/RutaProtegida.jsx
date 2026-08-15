import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/contextos';
import { Cargando } from './ui';

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

  // `null` significa "todavía no sabemos": con la sesión en una cookie httpOnly
  // hay que preguntarle al backend quién es, y eso tarda un viaje. Tratar ese
  // instante como "no autenticado" echaría al login a quien SÍ tiene sesión
  // cada vez que recarga la página en /carrito o /mis-compras.
  if (autenticado === null) {
    return <Cargando texto="Comprobando tu sesión…" />;
  }

  if (!autenticado) {
    // Se guarda de dónde venía para devolverlo ahí después de entrar.
    return <Navigate to="/login" state={{ desde: ubicacion.pathname }} replace />;
  }

  return children;
}

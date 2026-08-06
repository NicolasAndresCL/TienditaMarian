import { Link, useNavigate } from 'react-router-dom';
import { useAuth, useCarrito } from '../context/contextos';

export default function Navbar() {
  const { autenticado, usuario, salir } = useAuth();
  const { cantidadTotal } = useCarrito();
  const navegar = useNavigate();

  const alSalir = async () => {
    await salir();
    navegar('/');
  };

  return (
    <nav className="bg-white shadow px-6 py-3 flex items-center justify-between sticky top-0 z-10">
      <Link to="/" className="text-xl font-bold text-pink-700">
        🧸 Tiendita de Marian
      </Link>

      <div className="flex items-center gap-4">
        {autenticado ? (
          <>
            <Link to="/carrito" className="relative text-pink-700 font-semibold">
              🛒 Carrito
              {cantidadTotal > 0 && (
                <span className="absolute -top-2 -right-4 bg-pink-500 text-white text-xs rounded-full px-1.5 py-0.5">
                  {cantidadTotal}
                </span>
              )}
            </Link>

            <Link to="/mis-compras" className="text-pink-700">
              Mis compras
            </Link>

            <span className="text-sm text-gray-500">{usuario?.username}</span>

            {/* No existía ningún logout: `removeItem` no aparecía en el proyecto. */}
            <button onClick={alSalir} className="text-sm text-pink-600 underline">
              Salir
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="text-pink-700 font-semibold">
              Entrar
            </Link>
            <Link to="/registro" className="text-pink-700">
              Registrarme
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}

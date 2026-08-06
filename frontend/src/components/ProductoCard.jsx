import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, useCarrito } from '../context/contextos';
import { Boton, MensajeError } from './ui';

export default function ProductoCard({ producto }) {
  const { autenticado } = useAuth();
  const { agregar } = useCarrito();
  const navegar = useNavigate();

  const [agregando, setAgregando] = useState(false);
  const [error, setError] = useState(null);
  const [agregado, setAgregado] = useState(false);

  const sinStock = producto.stock <= 0;

  const alAgregar = async () => {
    if (!autenticado) {
      // Se recuerda desde dónde venía para volver aquí tras iniciar sesión.
      navegar('/login', { state: { desde: '/' } });
      return;
    }

    setAgregando(true);
    setError(null);

    // Esto era `alert('Producto agregado al carrito (simulado)')`: el frontend
    // fingía tener un carrito que el backend sí implementaba.
    const { ok, error: fallo } = await agregar(producto.id, 1);

    setAgregando(false);

    if (ok) {
      setAgregado(true);
      setTimeout(() => setAgregado(false), 2000);
    } else {
      setError(fallo);
    }
  };

  const texto = sinStock
    ? 'Agotado'
    : agregado
      ? '¡Agregado!'
      : agregando
        ? 'Agregando…'
        : '🛒 Agregar al carrito';

  return (
    <article className="bg-rose-100 rounded-lg shadow hover:shadow-lg transition duration-300 p-4 flex flex-col items-center outline-solid outline-pink-300">
      <div className="flex justify-center items-center bg-violet-100 h-48 w-full rounded-md overflow-hidden mb-4">
        {producto.image ? (
          <img
            src={producto.image}
            alt={producto.nombre}
            className="h-full object-contain"
            loading="lazy"
          />
        ) : (
          <span className="text-4xl">🧸</span>
        )}
      </div>

      <h3 className="text-lg font-bold text-gray-800 text-center mb-2 tracking-tight">
        🧸 {producto.nombre}
      </h3>
      <p className="text-sm text-gray-700 text-center mb-2">{producto.descripcion}</p>

      <p className="text-lg font-semibold text-pink-700 text-center">
        💲 ${Number(producto.precio).toLocaleString('es-CL')}
      </p>
      <p className="text-sm text-gray-600 text-center mb-3">
        {sinStock ? '😔 Sin stock' : `🧮 Quedan ${producto.stock}`}
      </p>

      <MensajeError error={error} onCerrar={() => setError(null)} />

      <Boton onClick={alAgregar} disabled={agregando || sinStock}>
        {texto}
      </Boton>
    </article>
  );
}

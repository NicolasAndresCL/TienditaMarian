import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { obtenerProducto } from '../services';
import { useAuth, useCarrito } from '../context/contextos';
import { Boton, Cargando, MensajeError } from '../components/ui';

/**
 * Detalle de un producto.
 *
 * `obtenerProducto(id)` llevaba tiempo escrito en los servicios y no lo llamaba
 * nadie: el backend servía `/productos/<id>/` y la tienda no tenía dónde
 * mostrarlo. Sin esta página, la descripción completa de un juguete solo cabía
 * recortada en su tarjeta del catálogo, y no había una URL que compartir.
 */
export default function Producto() {
  const { id } = useParams();
  const navegar = useNavigate();
  const { autenticado } = useAuth();
  const { agregar } = useCarrito();

  const [producto, setProducto] = useState(null);
  const [cantidad, setCantidad] = useState(1);
  const [error, setError] = useState(null);
  const [agregando, setAgregando] = useState(false);
  const [agregado, setAgregado] = useState(false);

  useEffect(() => {
    let vigente = true;
    obtenerProducto(id)
      .then((datos) => vigente && setProducto(datos))
      .catch((fallo) => vigente && setError(fallo));
    return () => {
      vigente = false;
    };
  }, [id]);

  const alAgregar = async () => {
    if (!autenticado) {
      navegar('/login', { state: { desde: `/producto/${id}` } });
      return;
    }

    setAgregando(true);
    setError(null);
    const { ok, error: fallo } = await agregar(producto.id, cantidad);
    setAgregando(false);

    if (ok) {
      setAgregado(true);
      setTimeout(() => setAgregado(false), 2000);
    } else {
      setError(fallo);
    }
  };

  if (error && !producto) return <MensajeError error={error} />;
  if (!producto) return <Cargando texto="Buscando el juguete…" />;

  const sinStock = producto.stock <= 0;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <Link to="/" className="text-pink-600 underline text-sm">
        ← Volver al catálogo
      </Link>

      <div className="mt-4 grid gap-8 md:grid-cols-2 bg-white rounded-lg shadow p-6">
        <div className="flex justify-center items-center bg-violet-100 rounded-md overflow-hidden h-80">
          {producto.image ? (
            <img src={producto.image} alt={producto.nombre} className="h-full object-contain" />
          ) : (
            <span className="text-7xl">🧸</span>
          )}
        </div>

        <div className="flex flex-col">
          <h1 className="text-3xl font-bold text-pink-700 mb-3">{producto.nombre}</h1>
          <p className="text-gray-700 mb-4">{producto.descripcion}</p>

          <p className="text-3xl font-bold text-pink-700 mb-1">
            ${Number(producto.precio).toLocaleString('es-CL')}
          </p>
          <p className="text-sm text-gray-600 mb-6">
            {sinStock ? '😔 Sin stock por ahora' : `🧮 Quedan ${producto.stock} disponibles`}
          </p>

          <MensajeError error={error} onCerrar={() => setError(null)} />

          {!sinStock && (
            <label className="block mb-4">
              <span className="block mb-1 text-sm font-medium text-pink-800">Cantidad</span>
              <input
                type="number"
                min="1"
                max={producto.stock}
                value={cantidad}
                onChange={(e) => setCantidad(Number(e.target.value))}
                className="w-24 px-3 py-2 border border-pink-200 rounded text-center"
              />
            </label>
          )}

          <Boton onClick={alAgregar} disabled={agregando || sinStock}>
            {sinStock
              ? 'Agotado'
              : agregado
                ? '¡Agregado!'
                : agregando
                  ? 'Agregando…'
                  : '🛒 Agregar al carrito'}
          </Boton>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { obtenerOrden, pagarOrden } from '../services';
import { Boton, Cargando, MensajeError } from '../components/ui';

export default function Compra() {
  const { id } = useParams();
  const [orden, setOrden] = useState(null);
  const [error, setError] = useState(null);
  const [pagando, setPagando] = useState(false);

  useEffect(() => {
    obtenerOrden(id).then(setOrden).catch(setError);
  }, [id]);

  // El botón de pagar no existía: la orden nacía "Pendiente" y no había forma de
  // cobrarla desde la tienda, aunque el backend supiera hacerlo.
  const alPagar = async () => {
    setPagando(true);
    setError(null);
    try {
      setOrden(await pagarOrden(id));
    } catch (fallo) {
      setError(fallo);
    } finally {
      setPagando(false);
    }
  };

  if (error && !orden) return <MensajeError error={error} />;
  if (!orden) return <Cargando texto="Buscando tu compra…" />;

  return (
    <div className="p-8 max-w-2xl mx-auto text-center">
      <h1 className="text-3xl font-bold text-pink-700 mb-2">
        {orden.pagado ? '¡Pago confirmado! 🎉' : '¡Gracias por tu compra! 🎉'}
      </h1>
      <p className="text-gray-600 mb-6">
        Tu orden <strong>#{orden.id}</strong> quedó registrada. Te enviamos un correo con el detalle.
      </p>

      <MensajeError error={error} onCerrar={() => setError(null)} />

      <ul className="bg-white rounded shadow divide-y text-left mb-6">
        {orden.items.map((item) => (
          <li key={item.id} className="p-4 flex justify-between">
            <span>
              {item.cantidad} × {item.producto.nombre}
            </span>
            <span className="font-semibold">
              ${Number(item.subtotal).toLocaleString('es-CL')}
            </span>
          </li>
        ))}
        <li className="p-4 flex justify-between text-xl font-bold text-pink-700">
          <span>Total</span>
          <span>${Number(orden.total).toLocaleString('es-CL')}</span>
        </li>
      </ul>

      {orden.pagado ? (
        <p className="mb-6 rounded bg-green-50 border border-green-200 text-green-700 p-3">
          Pago recibido. Estamos preparando tu pedido.
        </p>
      ) : (
        <div className="mb-6">
          <Boton onClick={alPagar} disabled={pagando}>
            {pagando ? 'Procesando el pago…' : `💳 Pagar $${Number(orden.total).toLocaleString('es-CL')}`}
          </Boton>
        </div>
      )}

      <Link to="/" className="text-pink-600 underline font-semibold">
        Volver a la tienda
      </Link>
    </div>
  );
}

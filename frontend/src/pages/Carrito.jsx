import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCarrito } from '../context/contextos';
import { Boton, MensajeError, Cargando, Vacio, Input } from '../components/ui';

export default function Carrito() {
  const { items, total, cargando, error, actualizar, quitar, comprar, limpiarError } = useCarrito();
  const [cupon, setCupon] = useState('');
  const [comprando, setComprando] = useState(false);
  const navegar = useNavigate();

  if (cargando) return <Cargando texto="Cargando tu carrito…" />;

  const alComprar = async () => {
    setComprando(true);
    const { ok, orden } = await comprar(cupon.trim() || undefined);
    setComprando(false);

    if (ok) navegar(`/compra/${orden.id}`);
  };

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold text-pink-700 mb-6">Tu carrito</h1>

      <MensajeError error={error} onCerrar={limpiarError} />

      {items.length === 0 ? (
        <Vacio texto="Tu carrito está vacío. ¡Ve a mirar la tienda!" />
      ) : (
        <>
          <ul className="space-y-4 mb-6">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex items-center gap-4 bg-white p-4 rounded shadow"
              >
                <div className="flex-grow">
                  <p className="font-semibold text-pink-800">{item.producto.nombre}</p>
                  <p className="text-sm text-gray-600">
                    ${Number(item.producto.precio).toLocaleString('es-CL')} c/u
                  </p>
                </div>

                <input
                  type="number"
                  min="1"
                  value={item.cantidad}
                  onChange={(e) => actualizar(item.producto.id, Number(e.target.value))}
                  className="w-20 px-2 py-1 border border-pink-200 rounded text-center"
                  aria-label={`Cantidad de ${item.producto.nombre}`}
                />

                <p className="w-28 text-right font-semibold text-pink-700">
                  ${Number(item.subtotal).toLocaleString('es-CL')}
                </p>

                <button
                  onClick={() => quitar(item.producto.id)}
                  className="text-red-500 hover:text-red-700 px-2"
                  aria-label={`Quitar ${item.producto.nombre}`}
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>

          <div className="bg-white p-4 rounded shadow">
            <Input
              label="¿Tienes un cupón?"
              type="text"
              value={cupon}
              onChange={(e) => setCupon(e.target.value)}
              placeholder="Ej: VERANO"
            />

            <p className="text-2xl font-bold text-right text-pink-700 mb-4">
              Total: ${Number(total).toLocaleString('es-CL')}
            </p>

            <Boton onClick={alComprar} disabled={comprando}>
              {comprando ? 'Confirmando…' : 'Confirmar compra'}
            </Boton>
          </div>
        </>
      )}
    </div>
  );
}

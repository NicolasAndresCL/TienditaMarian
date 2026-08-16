import { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { iniciarPagoWebpay, obtenerOrden, pagarOrden, redirigirAWebpay } from '../services';
import { Boton, Cargando, MensajeError } from '../components/ui';

// Cómo vuelve la clienta desde Transbank. El backend lo pone en la URL porque el
// retorno es un POST cross-site y no puede traer estado de sesión.
const MENSAJES_DE_VUELTA = {
  anulado: 'Cancelaste el pago. Tu orden sigue esperando.',
  rechazado: 'El pago fue rechazado. Puedes intentarlo de nuevo.',
  desconocido: 'No pudimos identificar ese pago. Si te cobraron, escríbenos.',
};

export default function Compra() {
  const { id } = useParams();
  const [parametros] = useSearchParams();
  const [orden, setOrden] = useState(null);
  const [error, setError] = useState(null);
  const [pagando, setPagando] = useState(false);

  const resultadoWebpay = parametros.get('pago');
  const avisoDeVuelta = MENSAJES_DE_VUELTA[resultadoWebpay];

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

  const alPagarConWebpay = async () => {
    setPagando(true);
    setError(null);
    try {
      // No hay `finally` que reactive el botón: si esto funciona, el navegador
      // ya se fue a Transbank y esta página deja de existir.
      redirigirAWebpay(await iniciarPagoWebpay(id));
    } catch (fallo) {
      setError(fallo);
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

      {avisoDeVuelta && !orden.pagado && (
        <p role="alert" className="mb-4 p-3 rounded bg-amber-50 border border-amber-200 text-amber-800 text-sm">
          {avisoDeVuelta}
        </p>
      )}

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
        <div className="mb-6 space-y-3">
          <Boton onClick={alPagarConWebpay} disabled={pagando}>
            {pagando ? 'Conectando con Webpay…' : `💳 Pagar $${Number(orden.total).toLocaleString('es-CL')} con Webpay`}
          </Boton>

          {/* La transferencia que la tienda confirma a mano: sigue siendo un
              medio de pago válido, no un botón de pruebas. */}
          <Boton onClick={alPagar} disabled={pagando} variante="secundario">
            {pagando ? 'Procesando…' : 'Pagar por transferencia'}
          </Boton>
        </div>
      )}

      <Link to="/" className="text-pink-600 underline font-semibold">
        Volver a la tienda
      </Link>
    </div>
  );
}

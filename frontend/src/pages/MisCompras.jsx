import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { obtenerOrdenes } from '../services';
import { Cargando, MensajeError, Vacio } from '../components/ui';

export default function MisCompras() {
  const [ordenes, setOrdenes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    obtenerOrdenes()
      .then(setOrdenes)
      .catch(setError)
      .finally(() => setCargando(false));
  }, []);

  if (cargando) return <Cargando texto="Buscando tus compras…" />;
  if (error) return <MensajeError error={error} />;

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold text-pink-700 mb-6">Mis compras</h1>

      {ordenes.length === 0 ? (
        <Vacio texto="Todavía no has comprado nada." />
      ) : (
        <ul className="space-y-3">
          {ordenes.map((orden) => (
            <li key={orden.id}>
              <Link
                to={`/compra/${orden.id}`}
                className="flex justify-between bg-white p-4 rounded shadow hover:shadow-md transition"
              >
                <span className="font-semibold text-pink-800">Orden #{orden.id}</span>
                <span className="text-gray-600">
                  {new Date(orden.creado).toLocaleDateString('es-CL')}
                </span>
                <span className="font-semibold">
                  ${Number(orden.total).toLocaleString('es-CL')}
                </span>
                <span className={orden.pagado ? 'text-green-600' : 'text-amber-600'}>
                  {orden.pagado ? 'Pagada' : 'Pendiente'}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

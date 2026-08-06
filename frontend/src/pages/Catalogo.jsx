import { useEffect, useState } from 'react';
import { obtenerProductos } from '../services';
import ProductoCard from '../components/ProductoCard';
import TituloCard from '../components/TituloCard';
import { Cargando, MensajeError, Vacio } from '../components/ui';

export default function Catalogo() {
  const [productos, setProductos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let vigente = true;

    obtenerProductos()
      .then((lista) => {
        // Si el componente se desmontó mientras la petición viajaba, no se
        // actualiza el estado (React avisaría de una fuga de memoria).
        if (vigente) setProductos(lista);
      })
      .catch((fallo) => {
        if (vigente) setError(fallo);
      })
      .finally(() => {
        if (vigente) setCargando(false);
      });

    return () => {
      vigente = false;
    };
  }, []);

  if (cargando) return <Cargando texto="Cargando productos…" />;

  return (
    <div className="p-8">
      <TituloCard />

      <MensajeError error={error} onCerrar={() => setError(null)} />

      {productos.length === 0 && !error ? (
        <Vacio texto="Todavía no hay productos en la tienda." />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {productos.map((producto) => (
            <ProductoCard key={producto.id} producto={producto} />
          ))}
        </div>
      )}
    </div>
  );
}

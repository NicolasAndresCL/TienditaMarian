/**
 * Piezas de interfaz compartidas.
 *
 * `Login.jsx` y `Register.jsx` eran ~85% el mismo archivo: mismo layout, mismo
 * botón y la MISMA clase de input copiada literalmente seis veces entre los dos.
 * Aquí se define una vez.
 */

export function Input({ label, ...props }) {
  return (
    <label className="block mb-4">
      {label && <span className="block mb-1 text-sm font-medium text-pink-800">{label}</span>}
      <input
        className="w-full px-3 py-2 border border-pink-200 rounded text-gray-800 placeholder-gray-500 bg-pink-50 focus:outline-none focus:ring-2 focus:ring-pink-400"
        {...props}
      />
    </label>
  );
}

export function Boton({ children, variante = 'primario', ...props }) {
  const estilos = {
    primario: 'bg-pink-400 text-white hover:bg-pink-500 disabled:bg-pink-200',
    secundario: 'bg-white text-pink-600 border border-pink-300 hover:bg-pink-50',
    enlace: 'text-pink-600 underline hover:text-pink-800 bg-transparent',
  };

  return (
    <button
      className={`w-full font-semibold py-2 rounded transition disabled:cursor-not-allowed ${estilos[variante]}`}
      {...props}
    >
      {children}
    </button>
  );
}

/**
 * Muestra el error del backend con su mensaje real.
 *
 * El código anterior hacía `catch { setError('...') }` sin capturar siquiera la
 * excepción, así que el mensaje del servidor —los errores de validación de DRF,
 * el "quedan 2 unidades" del stock— se perdía por completo.
 */
export function MensajeError({ error, onCerrar }) {
  if (!error) return null;

  return (
    <div role="alert" className="mb-4 p-3 rounded bg-red-50 border border-red-200 text-red-700 text-sm">
      <p>{error.mensaje ?? 'Ocurrió un error.'}</p>

      {error.codigo === 'stock_insuficiente' && error.detalle?.disponible !== undefined && (
        <p className="mt-1 font-semibold">
          Quedan {error.detalle.disponible} unidades disponibles.
        </p>
      )}

      {onCerrar && (
        <button type="button" onClick={onCerrar} className="mt-2 underline">
          Entendido
        </button>
      )}
    </div>
  );
}

export function Cargando({ texto = 'Cargando…' }) {
  return (
    <div className="flex items-center justify-center p-8 text-pink-700" role="status">
      {texto}
    </div>
  );
}

export function Vacio({ texto }) {
  // Antes, una lista vacía dejaba simplemente una grilla en blanco, sin explicar
  // nada al visitante.
  return <div className="p-8 text-center text-gray-500">{texto}</div>;
}

import { useState, useCallback, useEffect } from 'react';
import * as servicios from '../services';
import { CarritoContext, useAuth } from './contextos';

/**
 * El carrito, que hasta ahora NO EXISTÍA en el frontend.
 *
 * `carritoService.js` tenía las seis funciones escritas (61 líneas, incluido el
 * checkout) y nadie las importaba: el botón "Agregar al carrito" hacía
 * `alert('Producto agregado al carrito (simulado)')`. El backend tenía el
 * carrito, y el frontend fingía tenerlo.
 */
export function CarritoProvider({ children }) {
  const { autenticado } = useAuth();
  const [carrito, setCarrito] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);

  const refrescar = useCallback(async () => {
    if (!autenticado) {
      setCarrito(null);
      return;
    }

    setCargando(true);
    try {
      setCarrito(await servicios.obtenerCarrito());
      setError(null);
    } catch (fallo) {
      setError(fallo);
    } finally {
      setCargando(false);
    }
  }, [autenticado]);

  // Al entrar (o al cerrar sesión) el carrito se sincroniza con el servidor.
  useEffect(() => {
    refrescar();
  }, [refrescar]);

  /** Envuelve una operación: ejecuta, refresca y traduce el error. */
  const operar = useCallback(
    async (accion) => {
      setError(null);
      try {
        await accion();
        await refrescar();
        return { ok: true };
      } catch (fallo) {
        // El backend distingue los casos por código: `stock_insuficiente` trae
        // cuánto queda, así que la interfaz puede decir algo útil en vez de un
        // "error" genérico.
        setError(fallo);
        return { ok: false, error: fallo };
      }
    },
    [refrescar],
  );

  const agregar = useCallback(
    (productoId, cantidad = 1) => operar(() => servicios.agregarAlCarrito(productoId, cantidad)),
    [operar],
  );

  const actualizar = useCallback(
    (productoId, cantidad) => operar(() => servicios.actualizarCantidad(productoId, cantidad)),
    [operar],
  );

  const quitar = useCallback(
    (productoId) => operar(() => servicios.quitarDelCarrito(productoId)),
    [operar],
  );

  const vaciar = useCallback(() => operar(() => servicios.vaciarCarrito()), [operar]);

  const comprar = useCallback(
    async (cupon) => {
      setError(null);
      try {
        const orden = await servicios.checkout(cupon);
        await refrescar();
        return { ok: true, orden };
      } catch (fallo) {
        setError(fallo);
        return { ok: false, error: fallo };
      }
    },
    [refrescar],
  );

  const items = carrito?.items ?? [];
  const cantidadTotal = items.reduce((suma, item) => suma + item.cantidad, 0);

  const valor = {
    carrito,
    items,
    cantidadTotal,
    total: carrito?.total ?? '0.00',
    cargando,
    error,
    agregar,
    actualizar,
    quitar,
    vaciar,
    comprar,
    refrescar,
    limpiarError: () => setError(null),
  };

  return <CarritoContext.Provider value={valor}>{children}</CarritoContext.Provider>;
}


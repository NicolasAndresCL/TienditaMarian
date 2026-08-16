import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { AuthProvider } from '../context/AuthContext';
import { CarritoProvider } from '../context/CarritoContext';
import Catalogo from '../pages/Catalogo';
import Carrito from '../pages/Carrito';
import Producto from '../pages/Producto';
import { API, PRODUCTOS, errorDeApi, http, HttpResponse, servidor } from './servidor';

/**
 * El flujo que más duele si se rompe: ver el catálogo, agregar al carrito y
 * comprar. Los 12 tests que había cubrían el almacenamiento de la sesión y la
 * traducción de errores, pero **ni una interacción de la tienda**.
 *
 * Se monta la aplicación de verdad (contextos incluidos) contra una API
 * simulada a nivel de red: lo que se ejercita es el mismo cliente HTTP que corre
 * en producción, no un doble suyo.
 */

const USUARIA = { username: 'marian', email: 'marian@tiendita.cl', es_staff: false };

/** Declara que hay sesión iniciada. */
function conSesion() {
  servidor.use(http.get(`${API}/auth/me/`, () => HttpResponse.json(USUARIA)));
}

/** Declara el carrito que devuelve el backend.
 *
 * Devuelve un contador de llamadas para poder esperar a que la carga **termine**.
 * Hace falta porque un carrito vacío se ve igual que el estado inicial: un test
 * que solo compruebe "está vacío" pasa al instante, antes de que la petición
 * responda, y deja trabajo en vuelo que se resuelve durante el test siguiente —
 * que entonces falla por algo que no tiene nada que ver con él.
 */
function conCarrito(items = []) {
  const total = items
    .reduce((suma, i) => suma + Number(i.producto.precio) * i.cantidad, 0)
    .toFixed(2);

  const pedidos = { veces: 0 };
  servidor.use(
    http.get(`${API}/carrito/`, () => {
      pedidos.veces += 1;
      return HttpResponse.json({ id: 1, items, total });
    }),
  );
  return pedidos;
}

/**
 * Monta la página del carrito y espera a que TERMINE de cargar.
 *
 * Esperar por tiempo aquí no sirve, y este test lo demostró: cargar el carrito
 * son DOS peticiones encadenadas —`/auth/me/` primero, porque con la sesión en
 * una cookie httpOnly hay que preguntar quién es, y solo entonces `/carrito/`—
 * y el runner del CI es bastante más lento que una máquina de desarrollo. Con un
 * timeout de 3 s pasaba en local y fallaba en CI.
 *
 * El síntoma engaña además: se ve "Tu carrito está vacío", que es el estado
 * inicial legítimo mientras no se sabe si hay sesión, no un error.
 *
 * Así que se espera al HECHO de que el backend haya respondido —el contador del
 * handler— y no a que pase un rato. Eso no depende de la velocidad de nadie.
 */
async function montarCarritoCargado(items) {
  const pedidos = conCarrito(items);
  montar('/carrito');

  await waitFor(() => expect(pedidos.veces).toBeGreaterThan(0), { timeout: 10000 });
  return pedidos;
}

function itemDeCarrito(producto, cantidad) {
  return {
    id: producto.id,
    producto,
    cantidad,
    subtotal: (Number(producto.precio) * cantidad).toFixed(2),
  };
}

function montar(ruta = '/') {
  return render(
    <MemoryRouter initialEntries={[ruta]}>
      <AuthProvider>
        <CarritoProvider>
          <Routes>
            <Route path="/" element={<Catalogo />} />
            <Route path="/producto/:id" element={<Producto />} />
            <Route path="/carrito" element={<Carrito />} />
            <Route path="/login" element={<p>Pantalla de login</p>} />
            <Route path="/compra/:id" element={<p>Gracias por tu compra</p>} />
          </Routes>
        </CarritoProvider>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe('catálogo', () => {
  it('muestra los productos que devuelve la API', async () => {
    montar();

    expect(await screen.findByRole('link', { name: /Bugs Bunny/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Randall/ })).toBeInTheDocument();
  });

  it('marca como agotado lo que no tiene stock', async () => {
    montar();
    await screen.findByRole('link', { name: /Bugs Bunny/ });

    // Randall tiene stock 0 en la API simulada.
    expect(screen.getByRole('button', { name: /Agotado/ })).toBeDisabled();
  });

  it('avisa cuando la tienda no responde, con el mensaje del backend', async () => {
    servidor.use(
      http.get(`${API}/productos/`, () =>
        errorDeApi('error_servidor', 'Algo falló en el servidor.', {}, 500),
      ),
    );

    montar();

    expect(await screen.findByRole('alert')).toHaveTextContent(/Algo falló/);
  });
});

describe('agregar al carrito', () => {
  beforeEach(conSesion);

  it('manda al login a quien no tiene sesión', async () => {
    servidor.use(http.get(`${API}/auth/me/`, () => new HttpResponse(null, { status: 401 })));
    montar();
    await screen.findByRole('link', { name: /Bugs Bunny/ });

    await userEvent.click(screen.getAllByRole('button', { name: /Agregar al carrito/ })[0]);

    expect(await screen.findByText(/Pantalla de login/)).toBeInTheDocument();
  });

  it('agrega el producto y refresca el carrito', async () => {
    conCarrito();
    let agregado = null;
    servidor.use(
      http.post(`${API}/carrito/items/`, async ({ request }) => {
        agregado = await request.json();
        return HttpResponse.json({ id: 1, cantidad: agregado.cantidad });
      }),
    );

    montar();
    await screen.findByRole('link', { name: /Bugs Bunny/ });
    await userEvent.click(screen.getAllByRole('button', { name: /Agregar al carrito/ })[0]);

    await waitFor(() => expect(agregado).toEqual({ producto_id: 1, cantidad: 1 }));
    expect(await screen.findByRole('button', { name: /Agregado/ })).toBeInTheDocument();
  });

  it('muestra el detalle del stock cuando el backend rechaza por falta', async () => {
    conCarrito();
    servidor.use(
      http.post(`${API}/carrito/items/`, () =>
        errorDeApi(
          'stock_insuficiente',
          'No alcanza el stock de «Bugs Bunny»: pediste 3 y quedan 2.',
          { producto: 'Bugs Bunny', solicitado: 3, disponible: 2 },
          409,
        ),
      ),
    );

    montar();
    await screen.findByRole('link', { name: /Bugs Bunny/ });
    await userEvent.click(screen.getAllByRole('button', { name: /Agregar al carrito/ })[0]);

    const alerta = await screen.findByRole('alert');
    expect(alerta).toHaveTextContent(/pediste 3 y quedan 2/);
    // El dato del detalle, que es lo que el frontend usa para el aviso extra.
    expect(alerta).toHaveTextContent(/Quedan 2 unidades disponibles/);
  });
});

describe('detalle de producto', () => {
  it('muestra la descripción completa y permite elegir cantidad', async () => {
    conSesion();
    montar('/producto/1');

    expect(await screen.findByRole('heading', { name: 'Bugs Bunny' })).toBeInTheDocument();
    expect(screen.getByText(/Peluche clásico/)).toBeInTheDocument();
    expect(screen.getByRole('spinbutton')).toHaveValue(1);
  });

  it('avisa si el juguete no existe', async () => {
    conSesion();
    montar('/producto/999');

    expect(await screen.findByRole('alert')).toHaveTextContent(/no existe/);
  });
});

describe('carrito y compra', () => {
  beforeEach(conSesion);

  it('muestra los productos con su total', async () => {
    await montarCarritoCargado([itemDeCarrito(PRODUCTOS[0], 2)]);

    // En el carrito el nombre va en un <p>, no en un enlace como en el catálogo.
    expect(await screen.findByText('Bugs Bunny')).toBeInTheDocument();
    expect(screen.getByText(/Total: \$12.000/)).toBeInTheDocument();
  });

  it('dice que está vacío en vez de dejar la pantalla en blanco', async () => {
    // El helper ya espera a que el backend responda: un carrito vacío se ve
    // igual que el estado inicial, así que sin esa espera el test pasaría sin
    // haber comprobado nada.
    await montarCarritoCargado([]);

    expect(await screen.findByText(/carrito está vacío/)).toBeInTheDocument();
  });

  it('compra y lleva a la página de la orden', async () => {
    servidor.use(http.post(`${API}/checkout/`, () => HttpResponse.json({ id: 7 }, { status: 201 })));
    await montarCarritoCargado([itemDeCarrito(PRODUCTOS[0], 1)]);
    await userEvent.click(await screen.findByRole('button', { name: /Confirmar compra/ }));

    expect(await screen.findByText(/Gracias por tu compra/)).toBeInTheDocument();
  });

  it('no navega si el checkout falla, y explica por qué', async () => {
    servidor.use(
      http.post(`${API}/checkout/`, () =>
        errorDeApi('carrito_vacio', 'Tu carrito está vacío.', {}, 400),
      ),
    );
    await montarCarritoCargado([itemDeCarrito(PRODUCTOS[0], 1)]);
    await userEvent.click(await screen.findByRole('button', { name: /Confirmar compra/ }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/carrito está vacío/);
    expect(screen.queryByText(/Gracias por tu compra/)).not.toBeInTheDocument();
  });

  it('vacía el carrito entero de una vez', async () => {
    let vaciado = false;
    servidor.use(
      http.delete(`${API}/carrito/vaciar/`, () => {
        vaciado = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    await montarCarritoCargado([itemDeCarrito(PRODUCTOS[0], 1)]);
    await userEvent.click(await screen.findByRole('button', { name: /Vaciar carrito/ }));

    await waitFor(() => expect(vaciado).toBe(true));
  });
});

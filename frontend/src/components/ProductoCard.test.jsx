import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ProductoCard from './ProductoCard';

const agregarMock = vi.fn();
const navegarMock = vi.fn();
let autenticado = true;

vi.mock('../context/contextos', () => ({
  useAuth: () => ({ autenticado }),
  useCarrito: () => ({ agregar: agregarMock }),
}));

vi.mock('react-router-dom', async (importOriginal) => ({
  ...(await importOriginal()),
  useNavigate: () => navegarMock,
}));

const producto = {
  id: 1,
  nombre: 'Carrito Didáctico',
  descripcion: 'Para el desarrollo de los niños',
  precio: '3000.00',
  stock: 5,
  image: null,
};

function renderizar(props = {}) {
  return render(
    <MemoryRouter>
      <ProductoCard producto={{ ...producto, ...props }} />
    </MemoryRouter>,
  );
}

describe('ProductoCard', () => {
  beforeEach(() => {
    autenticado = true;
    agregarMock.mockReset().mockResolvedValue({ ok: true });
  });

  it('muestra el producto con su precio y su stock', () => {
    renderizar();

    expect(screen.getByText(/Carrito Didáctico/)).toBeInTheDocument();
    expect(screen.getByText(/Quedan 5/)).toBeInTheDocument();
  });

  it('agrega al carrito de verdad (antes era un alert de mentira)', async () => {
    renderizar();

    fireEvent.click(screen.getByRole('button'));

    await waitFor(() => expect(agregarMock).toHaveBeenCalledWith(1, 1));
  });

  it('manda al login si no hay sesión, en vez de agregar', () => {
    autenticado = false;
    renderizar();

    fireEvent.click(screen.getByRole('button'));

    expect(agregarMock).not.toHaveBeenCalled();
    expect(navegarMock).toHaveBeenCalledWith('/login', { state: { desde: '/' } });
  });

  it('deshabilita el botón si el producto está agotado', () => {
    renderizar({ stock: 0 });

    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByText(/Sin stock/)).toBeInTheDocument();
  });

  it('muestra el mensaje real del backend cuando falla', async () => {
    agregarMock.mockResolvedValue({
      ok: false,
      error: {
        codigo: 'stock_insuficiente',
        mensaje: 'No alcanza el stock.',
        detalle: { disponible: 2 },
      },
    });
    renderizar();

    fireEvent.click(screen.getByRole('button'));

    expect(await screen.findByRole('alert')).toHaveTextContent('No alcanza el stock.');
    expect(screen.getByText(/Quedan 2 unidades disponibles/)).toBeInTheDocument();
  });
});

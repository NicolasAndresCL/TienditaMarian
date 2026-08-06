import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { CarritoProvider } from './context/CarritoContext';
import Navbar from './components/Navbar';
import RutaProtegida from './components/RutaProtegida';
import Catalogo from './pages/Catalogo';
import Login from './pages/Login';
import Registro from './pages/Registro';
import Carrito from './pages/Carrito';
import Compra from './pages/Compra';
import MisCompras from './pages/MisCompras';

/**
 * App tenía 66 líneas que hacían de todo: pedir los productos con un axios
 * inline, guardar el token en un useState y "navegar" con dos banderas booleanas
 * (`showLogin`, `showRegister`) mediante un early-return que reemplazaba la
 * pantalla entera. No había URLs, ni enlaces compartibles, ni botón atrás.
 *
 * Ahora: router de verdad, estado en contextos y una página por pantalla.
 */
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        {/* El carrito va dentro de Auth: se sincroniza al entrar y se limpia al salir. */}
        <CarritoProvider>
          <div className="min-h-screen bg-pink-50">
            <Navbar />

            <Routes>
              <Route path="/" element={<Catalogo />} />
              <Route path="/login" element={<Login />} />
              <Route path="/registro" element={<Registro />} />

              <Route
                path="/carrito"
                element={
                  <RutaProtegida>
                    <Carrito />
                  </RutaProtegida>
                }
              />
              <Route
                path="/mis-compras"
                element={
                  <RutaProtegida>
                    <MisCompras />
                  </RutaProtegida>
                }
              />
              <Route
                path="/compra/:id"
                element={
                  <RutaProtegida>
                    <Compra />
                  </RutaProtegida>
                }
              />

              <Route
                path="*"
                element={<div className="p-8 text-center">Página no encontrada.</div>}
              />
            </Routes>
          </div>
        </CarritoProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

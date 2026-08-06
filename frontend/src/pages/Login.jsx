import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/contextos';
import { Input, Boton, MensajeError } from '../components/ui';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [enviando, setEnviando] = useState(false);

  const { entrar, error, limpiarError } = useAuth();
  const navegar = useNavigate();
  const ubicacion = useLocation();

  // Si llegó aquí por intentar algo que requería sesión, se vuelve a esa página
  // después de entrar en vez de mandarlo siempre al inicio.
  const destino = ubicacion.state?.desde ?? '/';

  const enviar = async (e) => {
    e.preventDefault();
    setEnviando(true);

    const exito = await entrar(username, password);

    setEnviando(false);
    if (exito) navegar(destino, { replace: true });
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-pink-50">
      <form onSubmit={enviar} className="bg-white p-8 rounded shadow-md w-80">
        <h1 className="text-2xl font-bold mb-6 text-center text-pink-700">Iniciar sesión</h1>

        <MensajeError error={error} onCerrar={limpiarError} />

        <Input
          label="Usuario"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          required
        />
        <Input
          label="Contraseña"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />

        <Boton type="submit" disabled={enviando}>
          {enviando ? 'Ingresando…' : 'Ingresar'}
        </Boton>

        <p className="mt-4 text-center text-sm">
          <Link to="/registro" className="text-pink-600 underline font-semibold">
            ¿No tienes cuenta? Regístrate
          </Link>
        </p>
      </form>
    </div>
  );
}

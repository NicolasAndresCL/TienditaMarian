import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/contextos';
import { Input, Boton, MensajeError } from '../components/ui';

export default function Registro() {
  const [datos, setDatos] = useState({
    username: '',
    email: '',
    password: '',
    passwordConfirm: '',
  });
  const [enviando, setEnviando] = useState(false);

  const { registrarse, error, limpiarError } = useAuth();
  const navegar = useNavigate();

  const cambiar = (campo) => (e) => setDatos({ ...datos, [campo]: e.target.value });

  const enviar = async (e) => {
    e.preventDefault();
    setEnviando(true);

    // El registro deja la sesión ya iniciada: el backend devuelve los tokens.
    // Antes había que volver a la pantalla de login e ingresar otra vez.
    const exito = await registrarse(datos);

    setEnviando(false);
    if (exito) navegar('/', { replace: true });
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-pink-50">
      <form onSubmit={enviar} className="bg-white p-8 rounded shadow-md w-80">
        <h1 className="text-2xl font-bold mb-6 text-center text-pink-700">Crear cuenta</h1>

        <MensajeError error={error} onCerrar={limpiarError} />

        <Input
          label="Usuario"
          type="text"
          value={datos.username}
          onChange={cambiar('username')}
          autoComplete="username"
          required
        />
        <Input
          label="Correo"
          type="email"
          value={datos.email}
          onChange={cambiar('email')}
          autoComplete="email"
          required
        />
        <Input
          label="Contraseña"
          type="password"
          value={datos.password}
          onChange={cambiar('password')}
          autoComplete="new-password"
          required
        />
        <Input
          label="Repite la contraseña"
          type="password"
          value={datos.passwordConfirm}
          onChange={cambiar('passwordConfirm')}
          autoComplete="new-password"
          required
        />

        <Boton type="submit" disabled={enviando}>
          {enviando ? 'Creando cuenta…' : 'Registrarme'}
        </Boton>

        <p className="mt-4 text-center text-sm">
          <Link to="/login" className="text-pink-600 underline font-semibold">
            ¿Ya tienes cuenta? Inicia sesión
          </Link>
        </p>
      </form>
    </div>
  );
}

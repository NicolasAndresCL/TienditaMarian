import { describe, it, expect, beforeEach } from 'vitest';
import { normalizarError } from './client';
import { leerTokenCsrf } from './tokens';

/**
 * El frontend no tenía NI UN test. Estos cubren lo que más duele si se rompe:
 * la sesión y la interpretación de los errores del backend.
 *
 * Los que probaban `guardarTokens`/`leerTokens` desaparecieron con lo que
 * probaban: los JWT ya no se guardan aquí, viven en cookies httpOnly que este
 * código no puede leer. Lo que sí queda del lado del navegador es el token
 * CSRF, que es lo que se prueba ahora.
 */

describe('token CSRF', () => {
  beforeEach(() => {
    // jsdom acumula cookies entre tests; se limpian caducándolas.
    document.cookie.split('; ').forEach((cookie) => {
      const nombre = cookie.split('=')[0];
      if (nombre) document.cookie = `${nombre}=; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
    });
  });

  it('lee el token de la cookie que deja el backend', () => {
    document.cookie = 'csrftoken=abc123';

    expect(leerTokenCsrf()).toBe('abc123');
  });

  it('lo encuentra aunque haya otras cookies delante', () => {
    document.cookie = 'otra=loquesea';
    document.cookie = 'csrftoken=xyz789';

    expect(leerTokenCsrf()).toBe('xyz789');
  });

  it('devuelve null si todavía no hay token', () => {
    expect(leerTokenCsrf()).toBeNull();
  });

  it('no confunde una cookie cuyo nombre TERMINA en csrftoken', () => {
    // `startsWith('csrftoken=')` sobre cada cookie ya separada evita el clásico
    // falso positivo de buscar la subcadena en la cadena entera.
    document.cookie = 'nocsrftoken=impostor';

    expect(leerTokenCsrf()).toBeNull();
  });
});

describe('normalizarError', () => {
  it('conserva el código y el mensaje del backend', () => {
    const error = {
      response: {
        status: 409,
        data: {
          error: {
            codigo: 'stock_insuficiente',
            mensaje: 'No alcanza el stock de «Muñeca»: pediste 3 y quedan 2.',
            detalle: { producto: 'Muñeca', solicitado: 3, disponible: 2 },
          },
        },
      },
    };

    expect(normalizarError(error)).toEqual({
      codigo: 'stock_insuficiente',
      mensaje: 'No alcanza el stock de «Muñeca»: pediste 3 y quedan 2.',
      detalle: { producto: 'Muñeca', solicitado: 3, disponible: 2 },
      status: 409,
    });
  });

  it('distingue un fallo de red de un error del servidor', () => {
    // Antes ambos casos mostraban el mismo texto genérico, porque el `catch` ni
    // siquiera capturaba la excepción.
    const sinConexion = normalizarError({ message: 'Network Error' });
    const servidorCaido = normalizarError({ response: { status: 500, data: '<html>' } });

    expect(sinConexion.codigo).toBe('sin_conexion');
    expect(servidorCaido.codigo).toBe('error_servidor');
    expect(servidorCaido.status).toBe(500);
  });

  it('nunca devuelve undefined como mensaje', () => {
    expect(normalizarError({}).mensaje).toBeTruthy();
  });
});

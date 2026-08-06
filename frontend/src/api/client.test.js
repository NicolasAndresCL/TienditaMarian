import { describe, it, expect, beforeEach } from 'vitest';
import { normalizarError } from './client';
import { guardarTokens, leerTokens, borrarTokens, haySesion } from './tokens';

/**
 * El frontend no tenía NI UN test. Estos cubren lo que más duele si se rompe:
 * la sesión y la interpretación de los errores del backend.
 */

describe('almacenamiento de la sesión', () => {
  beforeEach(() => localStorage.clear());

  it('guarda y recupera los dos tokens', () => {
    guardarTokens({ access: 'abc', refresh: 'xyz' });

    expect(leerTokens()).toEqual({ access: 'abc', refresh: 'xyz' });
  });

  it('guarda el refresh, que antes se descartaba', () => {
    guardarTokens({ access: 'abc', refresh: 'xyz' });

    expect(leerTokens().refresh).toBe('xyz');
  });

  it('borra la sesión entera al salir', () => {
    guardarTokens({ access: 'abc', refresh: 'xyz' });

    borrarTokens();

    expect(haySesion()).toBe(false);
    expect(leerTokens()).toEqual({ access: null, refresh: null });
  });

  it('sin tokens no hay sesión', () => {
    expect(haySesion()).toBe(false);
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

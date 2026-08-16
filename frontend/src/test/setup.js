import '@testing-library/jest-dom';
import { afterAll, afterEach, beforeAll, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import { servidor } from './servidor';

// `error` deja en evidencia cualquier petición que un test no haya declarado:
// una llamada inesperada es un fallo, no algo que se responde en silencio.
beforeAll(() => servidor.listen({ onUnhandledRequest: 'error' }));

afterEach(() => {
  cleanup();
  servidor.resetHandlers();
  localStorage.clear();
  vi.clearAllMocks();
});

afterAll(() => servidor.close());

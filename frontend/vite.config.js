/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

// El proyecto es ESM ("type": "module"), donde `__dirname` no existe.
const raiz = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [
    // Estaba en package.json pero NO registrado aquí. Sin él no había Fast
    // Refresh (cada edición recargaba la página entera y perdía el estado) y el
    // JSX se compilaba con el transform clásico — por eso todos los archivos
    // necesitaban `import React from 'react'` escrito a mano.
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(raiz, './src'),
    },
  },
  server: {
    port: 5173,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',

    // La suite trae sus propios valores de entorno, igual que
    // `config/settings/test.py` en el backend: así corre en un checkout limpio,
    // sin `.env` ni secretos — que es exactamente como corre en CI.
    //
    // Sin esto, `VITE_API_BASE_URL` quedaba en `undefined` en el pipeline
    // (`frontend/.env` está en .gitignore y allí no existe), el cliente pedía
    // `/undefined/api/v1/productos/`, MSW no reconocía esa URL y las peticiones
    // salían a la red de verdad. El síntoma era "No pudimos conectar con la
    // tienda", y en local nunca aparecía porque aquí sí hay `.env`.
    env: {
      VITE_API_BASE_URL: 'http://localhost:8000',
    },

    environmentOptions: {
      jsdom: { customExportConditions: [''] },
    },

    // El runner del CI es bastante más lento que una máquina de desarrollo:
    // montar jsdom + MSW y encadenar dos peticiones (/auth/me/ y luego
    // /carrito/) no cabía en los 5 s que vitest da por defecto, y los tests
    // morían con "Test timed out in 5000ms" — antes incluso de que su propia
    // espera interna se agotara. Aquí no se está tapando una carrera: los tests
    // esperan a hechos concretos, no a que pase un rato; esto solo les da margen
    // para que el reloj del test no los mate mientras esperan bien.
    testTimeout: 20000,
    hookTimeout: 20000,
  },
})

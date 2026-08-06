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
  },
})

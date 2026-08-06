import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';

// Ya no hace falta `import React from 'react'`: con el plugin de React
// registrado en vite.config.js, el JSX usa el transform automático.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

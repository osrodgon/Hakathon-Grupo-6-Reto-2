import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

/**
 * Punto de entrada principal de la aplicación React
 * Ratoncito Pérez Madrid - Aventura Familiar Interactiva
 */

// Configuración global de la aplicación
if (process.env.NODE_ENV === 'development') {
  console.log('🐭✨ Ratoncito Pérez Madrid App iniciando en modo desarrollo');
}

// Crear root de React 18
const root = ReactDOM.createRoot(document.getElementById('root'));

// Renderizar la aplicación
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Registrar service worker para PWA (opcional)
if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('SW registered: ', registration);
      })
      .catch((registrationError) => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}

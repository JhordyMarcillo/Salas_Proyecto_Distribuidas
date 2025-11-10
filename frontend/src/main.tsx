import React from 'react';
import ReactDOM from 'react-dom/client';
import 'primereact/resources/themes/lara-dark-teal/theme.css';  // Tema de PrimeReact (elige uno)
import 'primereact/resources/primereact.min.css';  // Estilos base
import 'primeicons/primeicons.css';  // Iconos
import App from './App.tsx';  // Componente principal

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
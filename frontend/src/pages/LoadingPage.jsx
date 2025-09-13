import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { COLORS, FONTS } from '../config/constants';

/**
 * Página de carga inicial con mensajes rotativos
 * @param {Object} props
 * @param {function} props.onComplete - Función a ejecutar cuando termine la carga
 */
const LoadingPage = ({ onComplete }) => {
  const [loadingMessage, setLoadingMessage] = useState('');

  // Mensajes de carga rotativos y motivadores
  const loadingMessages = [
    "El Ratoncito Pérez está preparando tu aventura mágica... ✨",
    "Despertando a los duendes de Madrid... 🏰",
    "Buscando moneditas por la ciudad... 💰",
    "Preparando historias increíbles... 📖",
    "El Ratoncito está afilando sus bigotes... 🐭",
    "Cargando la magia de Madrid... 🌟",
    "Preparando mapas secretos... 🗺️",
    "Organizando aventuras familiares... 👨‍👩‍👧‍👦"
  ];

  useEffect(() => {
    // Mostrar primer mensaje inmediatamente
    setLoadingMessage(loadingMessages[0]);

    // Cambiar mensajes cada 2 segundos
    const messageInterval = setInterval(() => {
      const randomMessage = loadingMessages[Math.floor(Math.random() * loadingMessages.length)];
      setLoadingMessage(randomMessage);
    }, 2000);

    // Completar carga después de 4.5 segundos
    const loadingTimer = setTimeout(() => {
      onComplete();
    }, 4500);

    // Cleanup
    return () => {
      clearInterval(messageInterval);
      clearTimeout(loadingTimer);
    };
  }, [onComplete]);

  return (
    <div 
      className="min-h-screen flex flex-col items-center justify-center px-6"
      style={{ backgroundColor: COLORS.BACKGROUND }}
    >
      {/* Contenedor principal */}
      <div className="text-center max-w-md mx-auto">
        
        {/* Spinner de carga con animación */}
        <div className="mb-8 animate-bounce-soft">
          <LoadingSpinner size="lg" showIcon={true} />
        </div>

        {/* Título principal */}
        <h1 
          className="text-3xl font-bold mb-6 font-title"
          style={{ color: COLORS.PRIMARY_BROWN }}
        >
          Iniciando la Aventura
        </h1>

        {/* Mensaje rotativo */}
        <div className="mb-8">
          <p 
            className="text-lg leading-relaxed font-body animate-pulse-glow"
            style={{ color: COLORS.BLACK }}
          >
            {loadingMessage}
          </p>
        </div>

        {/* Barra de progreso animada */}
        <div className="w-full max-w-xs mx-auto">
          <div 
            className="h-2 rounded-full overflow-hidden"
            style={{ backgroundColor: COLORS.GRAY_LIGHT }}
          >
            <div 
              className="h-full rounded-full animate-pulse"
              style={{ 
                backgroundColor: COLORS.PRIMARY_YELLOW,
                width: '100%',
                animation: 'progressBar 6s ease-in-out forwards'
              }}
            />
          </div>
          <p 
            className="text-sm mt-2 font-body"
            style={{ color: COLORS.PRIMARY_BROWN }}
          >
            Preparando experiencia mágica...
          </p>
        </div>

        {/* Elementos decorativos */}
        <div className="mt-8 flex justify-center space-x-4">
          <div 
            className="w-3 h-3 rounded-full animate-bounce"
            style={{ 
              backgroundColor: COLORS.SECONDARY_RED,
              animationDelay: '0ms'
            }}
          />
          <div 
            className="w-3 h-3 rounded-full animate-bounce"
            style={{ 
              backgroundColor: COLORS.PRIMARY_YELLOW,
              animationDelay: '200ms'
            }}
          />
          <div 
            className="w-3 h-3 rounded-full animate-bounce"
            style={{ 
              backgroundColor: COLORS.SECONDARY_BLUE,
              animationDelay: '400ms'
            }}
          />
        </div>
      </div>

      {/* Styles para la animación de la barra de progreso */}
      <style jsx>{`
        @keyframes progressBar {
          from {
            width: 0%;
          }
          to {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
};

export default LoadingPage;

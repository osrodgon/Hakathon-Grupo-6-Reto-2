import React, { useState } from 'react';
import { Play, User, Home, MessageCircle, Map, Users, Camera } from 'lucide-react';
import { COLORS } from '../../config/constants';

/**
 * Menú de navegación flotante
 * @param {Object} props
 * @param {function} props.onNavigate - Función para manejar la navegación
 * @param {string} props.currentScreen - Pantalla actual
 */
const FloatingMenu = ({ onNavigate, currentScreen }) => {
  const [menuOpen, setMenuOpen] = useState(false);

  // Configuración de elementos del menú
  const menuItems = [
    { 
      id: 'profile', 
      icon: User, 
      label: 'Perfil',
      color: COLORS.SECONDARY_BLUE 
    },
    { 
      id: 'home', 
      icon: Home, 
      label: 'Inicio',
      color: COLORS.SECONDARY_BLUE 
    },
    { 
      id: 'chat', 
      icon: MessageCircle, 
      label: 'Chat',
      color: COLORS.SECONDARY_BLUE 
    },
    { 
      id: 'camera', 
      icon: Camera, 
      label: 'Cámara',
      color: COLORS.SECONDARY_BLUE 
    },
    { 
      id: 'map', 
      icon: Map, 
      label: 'Mapa',
      color: COLORS.SECONDARY_BLUE 
    },
    { 
      id: 'about', 
      icon: Users, 
      label: 'Nosotros',
      color: COLORS.SECONDARY_BLUE 
    }
  ];

  const handleNavigation = (screenId) => {
    onNavigate(screenId);
    setMenuOpen(false);
  };

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };

  return (
    <div className={`fixed top-4 right-4 z-50 transition-all duration-300 ${menuOpen ? 'w-48' : 'w-12'}`}>
      {/* Botón principal del menú */}
      <button
        onClick={toggleMenu}
        className="w-12 h-12 rounded-full shadow-lg flex items-center justify-center transform transition-all duration-300 hover:scale-110 active:scale-95"
        style={{ backgroundColor: COLORS.SECONDARY_RED }}
        aria-label="Abrir menú de navegación"
      >
        <Play 
          className={`w-6 h-6 transition-transform duration-300 ${menuOpen ? 'rotate-90' : ''}`}
          style={{ color: COLORS.WHITE }} 
        />
      </button>
      
      {/* Menú desplegable */}
      {menuOpen && (
        <div 
          className="mt-2 rounded-lg shadow-xl overflow-hidden animate-pulse-glow"
          style={{ backgroundColor: COLORS.WHITE }}
        >
          <div className="p-2">
            {menuItems.map((item) => {
              const IconComponent = item.icon;
              const isActive = currentScreen === item.id;
              
              return (
                <button 
                  key={item.id}
                  onClick={() => handleNavigation(item.id)}
                  className={`
                    w-full p-3 text-left rounded-lg flex items-center gap-3
                    transform transition-all duration-200
                    hover:scale-105 active:scale-95
                    ${isActive ? 'shadow-md' : 'hover:shadow-sm'}
                  `}
                  style={{
                    backgroundColor: isActive ? COLORS.PRIMARY_YELLOW : 'transparent',
                    color: COLORS.BLACK
                  }}
                >
                  <IconComponent 
                    className="w-5 h-5" 
                    style={{ color: item.color }} 
                  />
                  <span className="font-body font-medium">
                    {item.label}
                  </span>
                  
                  {/* Indicador de pantalla activa */}
                  {isActive && (
                    <div 
                      className="ml-auto w-2 h-2 rounded-full"
                      style={{ backgroundColor: COLORS.SECONDARY_RED }}
                    />
                  )}
                </button>
              );
            })}
          </div>
          
          {/* Información adicional */}
          <div 
            className="px-3 py-2 text-xs text-center border-t"
            style={{ 
              backgroundColor: COLORS.BACKGROUND,
              color: COLORS.PRIMARY_BROWN,
              borderColor: COLORS.GRAY_LIGHT
            }}
          >
            Ratoncito Pérez Madrid ✨
          </div>
        </div>
      )}
      
      {/* Overlay para cerrar el menú al hacer click fuera */}
      {menuOpen && (
        <div 
          className="fixed inset-0 -z-10"
          onClick={() => setMenuOpen(false)}
        />
      )}
    </div>
  );
};

export default FloatingMenu;

import React from 'react';
import { Crown } from 'lucide-react';
import { COLORS } from '../../config/constants';
import app2 from '../../images/app2.png';

/**
 * Componente de spinner de carga reutilizable
 * @param {Object} props
 * @param {string} props.size - Tamaño del spinner ('sm', 'md', 'lg')
 * @param {string} props.color - Color del spinner
 * @param {boolean} props.showIcon - Mostrar icono en el centro
 * @param {string} props.className - Clases CSS adicionales
 */
const LoadingSpinner = ({ 
  size = 'md', 
  color = COLORS.PRIMARY_YELLOW,
  showIcon = true,
  className = '' 
}) => {  // Configuración de tamaños - monedita más grande para móviles
  const sizeConfig = {
    sm: { spinner: 'w-8 h-8', icon: 'w-6 h-6' },
    md: { spinner: 'w-16 h-16', icon: 'w-12 h-12' },
    lg: { spinner: 'w-32 h-32', icon: 'w-24 h-24' }
  };

  const currentSize = sizeConfig[size] || sizeConfig.md;

  return (
    <div className={`relative inline-block ${className}`}>
      {/* Spinner animado */}
      <div 
        className={`${currentSize.spinner} border-4 rounded-full animate-spin`}
        style={{ 
          borderColor: color, 
          borderTopColor: 'transparent' 
        }}
      />
        {/* Icono central opcional */}
      {showIcon && (
        <div className="absolute inset-0 flex items-center justify-center">
          <img 
            src={app2}
            alt="Monedita mágica"
            className={`${currentSize.icon} object-contain animate-pulse`}
          />
        </div>
      )}
    </div>
  );
};

export default LoadingSpinner;

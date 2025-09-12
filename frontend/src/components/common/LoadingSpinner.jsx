import React from 'react';
import { Crown } from 'lucide-react';
import { COLORS } from '../../config/constants';

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
}) => {
  // Configuración de tamaños
  const sizeConfig = {
    sm: { spinner: 'w-8 h-8', icon: 'w-4 h-4' },
    md: { spinner: 'w-16 h-16', icon: 'w-8 h-8' },
    lg: { spinner: 'w-32 h-32', icon: 'w-16 h-16' }
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
          <Crown 
            className={currentSize.icon}
            style={{ color: COLORS.PRIMARY_BROWN }} 
          />
        </div>
      )}
    </div>
  );
};

export default LoadingSpinner;

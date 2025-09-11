import React from 'react';
import { COLORS, FONTS } from '../../config/constants';

/**
 * Componente de tarjeta reutilizable
 * @param {Object} props
 * @param {React.ReactNode} props.children - Contenido de la tarjeta
 * @param {string} props.className - Clases CSS adicionales
 * @param {boolean} props.hoverable - Si la tarjeta debe tener efecto hover
 * @param {function} props.onClick - Función a ejecutar al hacer click
 * @param {string} props.padding - Padding de la tarjeta ('none', 'sm', 'md', 'lg')
 * @param {boolean} props.shadow - Si mostrar sombra
 */
const Card = ({
  children,
  className = '',
  hoverable = false,
  onClick = null,
  padding = 'md',
  shadow = true,
  ...props
}) => {
  // Configuraciones de padding
  const paddingConfig = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6'
  };

  const currentPadding = paddingConfig[padding] || paddingConfig.md;

  const cardStyle = {
    backgroundColor: COLORS.WHITE,
    borderRadius: '12px',
    fontFamily: FONTS.BODY,
    cursor: onClick ? 'pointer' : 'default'
  };

  const cardClasses = `
    ${currentPadding}
    ${shadow ? 'shadow-lg' : ''}
    ${hoverable || onClick ? 'transform transition-all duration-300 hover:scale-105 hover:shadow-xl' : ''}
    ${className}
  `;

  const handleClick = (e) => {
    if (onClick) {
      onClick(e);
    }
  };

  return (
    <div
      style={cardStyle}
      className={cardClasses}
      onClick={handleClick}
      {...props}
    >
      {children}
    </div>
  );
};

/**
 * Componente de encabezado de tarjeta
 */
export const CardHeader = ({ children, className = '' }) => (
  <div className={`mb-4 ${className}`}>
    {children}
  </div>
);

/**
 * Componente de título de tarjeta
 */
export const CardTitle = ({ children, className = '', size = 'lg' }) => {
  const sizeClasses = {
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-2xl',
    xl: 'text-3xl'
  };

  return (
    <h3 
      className={`font-title font-bold ${sizeClasses[size]} ${className}`}
      style={{ color: COLORS.PRIMARY_BROWN }}
    >
      {children}
    </h3>
  );
};

/**
 * Componente de contenido de tarjeta
 */
export const CardContent = ({ children, className = '' }) => (
  <div className={`font-body ${className}`} style={{ color: COLORS.BLACK }}>
    {children}
  </div>
);

/**
 * Componente de pie de tarjeta
 */
export const CardFooter = ({ children, className = '' }) => (
  <div className={`mt-4 pt-4 border-t border-gray-200 ${className}`}>
    {children}
  </div>
);

export default Card;

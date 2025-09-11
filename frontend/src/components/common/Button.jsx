import React from 'react';
import { COLORS, FONTS } from '../../config/constants';

/**
 * Componente de botón reutilizable con diferentes variantes
 * @param {Object} props
 * @param {string} props.variant - Variante del botón ('primary', 'secondary', 'outline', 'danger')
 * @param {string} props.size - Tamaño del botón ('sm', 'md', 'lg')
 * @param {boolean} props.disabled - Estado deshabilitado
 * @param {boolean} props.loading - Estado de carga
 * @param {React.ReactNode} props.icon - Icono a mostrar
 * @param {string} props.className - Clases CSS adicionales
 * @param {React.ReactNode} props.children - Contenido del botón
 * @param {function} props.onClick - Función a ejecutar al hacer click
 */
const Button = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon = null,
  className = '',
  children,
  onClick,
  ...props
}) => {
  // Configuraciones de variantes
  const variants = {
    primary: {
      backgroundColor: COLORS.PRIMARY_YELLOW,
      color: COLORS.BLACK,
      hoverBg: COLORS.PRIMARY_BROWN,
      hoverColor: COLORS.WHITE
    },
    secondary: {
      backgroundColor: COLORS.SECONDARY_BLUE,
      color: COLORS.WHITE,
      hoverBg: COLORS.SECONDARY_RED,
      hoverColor: COLORS.WHITE
    },
    outline: {
      backgroundColor: 'transparent',
      color: COLORS.PRIMARY_BROWN,
      border: `2px solid ${COLORS.PRIMARY_YELLOW}`,
      hoverBg: COLORS.PRIMARY_YELLOW,
      hoverColor: COLORS.BLACK
    },
    danger: {
      backgroundColor: COLORS.SECONDARY_RED,
      color: COLORS.WHITE,
      hoverBg: '#dc2626',
      hoverColor: COLORS.WHITE
    }
  };

  // Configuraciones de tamaños
  const sizes = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-3 text-base',
    lg: 'px-6 py-4 text-lg'
  };

  const currentVariant = variants[variant] || variants.primary;
  const currentSize = sizes[size] || sizes.md;

  const buttonStyle = {
    backgroundColor: disabled ? COLORS.GRAY_MEDIUM : currentVariant.backgroundColor,
    color: disabled ? COLORS.GRAY_DARK : currentVariant.color,
    border: currentVariant.border || 'none',
    fontFamily: FONTS.BODY,
    transition: 'all 0.3s ease',
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.6 : 1
  };

  const handleClick = (e) => {
    if (!disabled && !loading && onClick) {
      onClick(e);
    }
  };

  return (
    <button
      style={buttonStyle}
      className={`
        ${currentSize}
        rounded-lg font-semibold
        transform transition-all duration-300
        hover:scale-105 active:scale-95
        focus:outline-none focus:ring-2 focus:ring-offset-2
        disabled:transform-none disabled:hover:scale-100
        ${className}
      `}
      onClick={handleClick}
      disabled={disabled || loading}
      {...props}
    >
      <div className="flex items-center justify-center gap-2">
        {loading && (
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        )}
        {!loading && icon && (
          <span className="flex items-center">
            {icon}
          </span>
        )}
        {children && (
          <span>{children}</span>
        )}
      </div>
    </button>
  );
};

export default Button;

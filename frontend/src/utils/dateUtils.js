/**
 * Utilidades para el manejo de fechas y tiempo
 */

/**
 * Formatea un timestamp a hora legible
 * @param {Date} timestamp - Fecha a formatear
 * @returns {string} Hora formateada (HH:MM)
 */
export const formatTime = (timestamp) => {
  return new Intl.DateTimeFormat('es-ES', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(timestamp);
};

/**
 * Obtiene el saludo apropiado según la hora del día
 * @returns {string} Saludo personalizado
 */
export const getTimeBasedGreeting = () => {
  const hour = new Date().getHours();
  
  if (hour < 12) {
    return '¡Buenos días';
  } else if (hour < 18) {
    return '¡Buenas tardes';
  } else {
    return '¡Buenas noches';
  }
};

/**
 * Calcula la diferencia de tiempo entre dos fechas
 * @param {Date} startTime - Tiempo inicial
 * @param {Date} endTime - Tiempo final  
 * @returns {number} Diferencia en minutos
 */
export const getTimeDifference = (startTime, endTime) => {
  return Math.floor((endTime - startTime) / (1000 * 60));
};

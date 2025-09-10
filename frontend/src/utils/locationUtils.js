/**
 * Utilidades para geolocalización y mapas
 */

/**
 * Obtiene la ubicación actual del usuario
 * @returns {Promise<{lat: number, lng: number}>} Coordenadas del usuario
 */
export const getCurrentLocation = () => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocalización no soportada'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lng: position.coords.longitude
        });
      },
      (error) => {
        console.warn('Error obteniendo ubicación:', error);
        // Ubicación por defecto: Puerta del Sol, Madrid
        resolve({ lat: 40.4168, lng: -3.7038 });
      },
      {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 600000 // 10 minutos
      }
    );
  });
};

/**
 * Calcula la distancia entre dos puntos usando la fórmula Haversine
 * @param {Object} point1 - {lat, lng}
 * @param {Object} point2 - {lat, lng}
 * @returns {number} Distancia en kilómetros
 */
export const calculateDistance = (point1, point2) => {
  const R = 6371; // Radio de la Tierra en km
  const dLat = toRadians(point2.lat - point1.lat);
  const dLng = toRadians(point2.lng - point1.lng);
  
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(point1.lat)) * Math.cos(toRadians(point2.lat)) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

/**
 * Convierte grados a radianes
 * @param {number} degrees 
 * @returns {number} Radianes
 */
const toRadians = (degrees) => {
  return degrees * (Math.PI / 180);
};

/**
 * Encuentra los lugares más cercanos al usuario
 * @param {Object} userLocation - {lat, lng}
 * @param {Array} places - Array de lugares
 * @param {number} limit - Número máximo de lugares a retornar
 * @returns {Array} Lugares ordenados por distancia
 */
export const getNearbyPlaces = (userLocation, places, limit = 5) => {
  if (!userLocation) return places.slice(0, limit);
  
  return places
    .map(place => ({
      ...place,
      distance: calculateDistance(userLocation, place)
    }))
    .sort((a, b) => a.distance - b.distance)
    .slice(0, limit);
};

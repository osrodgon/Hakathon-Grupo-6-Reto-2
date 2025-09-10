/**
 * Datos de lugares emblemáticos de Madrid con información turística y cultural
 * Incluye historias mágicas para niños y datos históricos para adultos
 */

export const MADRID_PLACES = [
  {
    id: 1,
    name: "Puerta del Sol",
    lat: 40.4168,
    lng: -3.7038,
    category: "centro-historico",
    description: "El corazón de Madrid donde el Ratoncito Pérez tiene su oficina secreta",
    historicalInfo: "La Puerta del Sol es el centro neurálgico de Madrid desde el siglo XVIII. Aquí se encuentra el kilómetro cero de las carreteras radiales españolas.",
    magicalStory: "¿Sabías que debajo del reloj de la Puerta del Sol hay un túnel secreto donde el Ratoncito Pérez guarda todas las cartas de los niños de Madrid?",
    childActivity: "Cuenta las campanadas del reloj y haz un deseo mágico",
    parentInfo: "Punto de partida ideal para rutas familiares por el Madrid de los Austrias",
    accessibility: {
      wheelchair: true,
      elevator: true,
      restrooms: true
    },
    openingHours: "24 horas",
    nearbyServices: ["metro", "autobuses", "restaurantes", "tiendas"]
  },
  {
    id: 2,
    name: "Palacio Real",
    lat: 40.4179,
    lng: -3.7146,
    category: "palacio",
    description: "El palacio donde el Ratoncito Pérez una vez visitó al Rey",
    historicalInfo: "Construido en el siglo XVIII, es uno de los palacios reales más grandes de Europa con 3.418 habitaciones.",
    magicalStory: "Una noche, el Ratoncito Pérez se coló en el Palacio Real para recoger un diente del príncipe. ¡Pero se perdió en las 3.418 habitaciones!",
    childActivity: "Imagina ser un príncipe o princesa y busca las habitaciones más bonitas",
    parentInfo: "Visitas guiadas familiares disponibles con actividades especiales para niños",
    accessibility: {
      wheelchair: true,
      elevator: true,
      restrooms: true
    },
    openingHours: "10:00 - 20:00 (Oct-Mar) / 10:00 - 19:00 (Abr-Sep)",
    nearbyServices: ["jardines", "cafetería", "tienda", "audioguías"]
  },
  {
    id: 3,
    name: "Plaza Mayor",
    lat: 40.4155,
    lng: -3.7074,
    category: "plaza",
    description: "La plaza donde se celebran las fiestas más divertidas",
    historicalInfo: "Construida en el siglo XVII, ha sido testigo de mercados, corridas de toros, autos de fe y celebraciones reales.",
    magicalStory: "En la Plaza Mayor, el Ratoncito Pérez organiza carreras nocturnas con sus amigos ratones. ¡El ganador se lleva el queso más grande!",
    childActivity: "Cuenta los arcos de la plaza y busca la estatua del Rey Felipe III",
    parentInfo: "Perfecto para descansar mientras los niños corren por el amplio espacio peatonal",
    accessibility: {
      wheelchair: true,
      elevator: false,
      restrooms: true
    },
    openingHours: "24 horas",
    nearbyServices: ["restaurantes", "cafeterías", "tiendas-souvenirs", "artistas-callejeros"]
  },
  {
    id: 4,
    name: "Parque del Retiro",
    lat: 40.4153,
    lng: -3.6844,
    category: "parque",
    description: "El parque favorito del Ratoncito Pérez para sus picnics",
    historicalInfo: "Antiguo parque real del siglo XVII, declarado Patrimonio de la Humanidad por la UNESCO en 2021.",
    magicalStory: "En el Parque del Retiro hay un árbol especial donde el Ratoncito Pérez esconde regalos para los niños más aventureros.",
    childActivity: "Busca el Palacio de Cristal y haz sombras divertidas con las manos",
    parentInfo: "Ideal para picnics familiares con múltiples zonas de juegos infantiles",
    accessibility: {
      wheelchair: true,
      elevator: false,
      restrooms: true
    },
    openingHours: "06:00 - 24:00 (Oct-Mar) / 06:00 - 02:00 (Abr-Sep)",
    nearbyServices: ["zonas-juegos", "estanque", "cafeterías", "alquiler-barcas"]
  },
  {
    id: 5,
    name: "Museo del Prado",
    lat: 40.4138,
    lng: -3.6921,
    category: "museo",
    description: "El museo donde el Ratoncito Pérez aprende sobre arte",
    historicalInfo: "Uno de los museos de arte más importantes del mundo, inaugurado en 1819 con obras maestras del arte español.",
    magicalStory: "El Ratoncito Pérez tiene un cuadro secreto en el Prado donde él aparece junto a Las Meninas de Velázquez",
    childActivity: "Juego de búsqueda: encuentra a las Meninas y cuenta cuántos perros hay en los cuadros",
    parentInfo: "Actividades familiares especiales los fines de semana y entrada gratuita para menores",
    accessibility: {
      wheelchair: true,
      elevator: true,
      restrooms: true
    },
    openingHours: "10:00 - 20:00 (L-S) / 10:00 - 19:00 (D)",
    nearbyServices: ["audioguías-niños", "cafetería", "tienda", "talleres-familiares"]
  },
  {
    id: 6,
    name: "Templo de Debod",
    lat: 40.4240,
    lng: -3.7178,
    category: "monumento",
    description: "El templo egipcio donde el Ratoncito Pérez viaja en el tiempo",
    historicalInfo: "Auténtico templo egipcio del siglo II a.C., donado por Egipto a España en 1968.",
    magicalStory: "El Ratoncito Pérez descubrió que este templo es una máquina del tiempo que lo lleva al antiguo Egipto",
    childActivity: "Imagina ser un explorador egipcio y busca jeroglíficos misteriosos",
    parentInfo: "Perfecto para enseñar historia antigua de forma divertida, con vistas espectaculares al atardecer",
    accessibility: {
      wheelchair: true,
      elevator: false,
      restrooms: true
    },
    openingHours: "10:00 - 20:00 (Abr-Sep) / 09:45 - 18:15 (Oct-Mar)",
    nearbyServices: ["mirador", "jardines", "cafetería-cercana"]
  }
];

/**
 * Categorías de lugares para filtrado
 */
export const PLACE_CATEGORIES = {
  CENTRO_HISTORICO: 'centro-historico',
  PALACIO: 'palacio', 
  PLAZA: 'plaza',
  PARQUE: 'parque',
  MUSEO: 'museo',
  MONUMENTO: 'monumento'
};

/**
 * Función para obtener lugares por categoría
 */
export const getPlacesByCategory = (category) => {
  return MADRID_PLACES.filter(place => place.category === category);
};

/**
 * Función para obtener lugar por ID
 */
export const getPlaceById = (id) => {
  return MADRID_PLACES.find(place => place.id === id);
};

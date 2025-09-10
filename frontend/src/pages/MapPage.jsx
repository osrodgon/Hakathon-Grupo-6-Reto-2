import React, { useState, useEffect } from 'react';
import { MapPin, Star, Clock, Users, Accessibility } from 'lucide-react';
import Button from '../components/common/Button';
import Card, { CardTitle, CardContent } from '../components/common/Card';
import { COLORS } from '../config/constants';
import { MADRID_PLACES, getPlacesByCategory } from '../data/madridPlaces';
import { getNearbyPlaces } from '../utils/locationUtils';

/**
 * Página de mapa interactivo con lugares de Madrid
 * @param {Object} props
 * @param {Object} props.userProfile - Perfil del usuario
 * @param {function} props.onNavigate - Función de navegación
 * @param {function} props.addSystemMessage - Función para añadir mensajes al chat
 * @param {Object} props.userLocation - Ubicación actual del usuario
 */
const MapPage = ({ 
  userProfile, 
  onNavigate, 
  addSystemMessage, 
  userLocation 
}) => {
  const [selectedPlace, setSelectedPlace] = useState(null);
  const [filteredPlaces, setFilteredPlaces] = useState(MADRID_PLACES);
  const [activeFilter, setActiveFilter] = useState('all');

  // Actualizar lugares cuando cambie la ubicación del usuario
  useEffect(() => {
    if (userLocation) {
      const nearbyPlaces = getNearbyPlaces(userLocation, MADRID_PLACES, 10);
      setFilteredPlaces(nearbyPlaces);
    }
  }, [userLocation]);

  /**
   * Filtros disponibles para los lugares
   */
  const filters = [
    { 
      id: 'all', 
      label: userProfile.language === 'en' ? 'All' : 'Todos',
      icon: Star 
    },
    { 
      id: 'centro-historico', 
      label: userProfile.language === 'en' ? 'Historic Center' : 'Centro Histórico',
      icon: MapPin 
    },
    { 
      id: 'parque', 
      label: userProfile.language === 'en' ? 'Parks' : 'Parques',
      icon: Users 
    },
    { 
      id: 'museo', 
      label: userProfile.language === 'en' ? 'Museums' : 'Museos',
      icon: Star 
    }
  ];

  /**
   * Maneja el filtrado de lugares
   */
  const handleFilter = (filterId) => {
    setActiveFilter(filterId);
    
    if (filterId === 'all') {
      setFilteredPlaces(
        userLocation 
          ? getNearbyPlaces(userLocation, MADRID_PLACES, 10)
          : MADRID_PLACES
      );
    } else {
      const categoryPlaces = getPlacesByCategory(filterId);
      setFilteredPlaces(
        userLocation 
          ? getNearbyPlaces(userLocation, categoryPlaces, 10)
          : categoryPlaces
      );
    }
  };

  /**
   * Maneja la selección de un lugar
   */
  const handlePlaceSelect = (place) => {
    setSelectedPlace(place);
  };

  /**
   * Explora un lugar con el Ratoncito Pérez
   */
  const explorePlaceWithRatoncito = (place) => {
    const isChild = userProfile.type === 'child';
    const isEnglish = userProfile.language === 'en';
    
    let message;
    if (isEnglish) {
      message = isChild
        ? `🐭✨ You've selected ${place.name}! ${place.magicalStory}`
        : `You've selected ${place.name}. ${place.historicalInfo}`;
    } else {
      message = isChild
        ? `🐭✨ ¡Has seleccionado ${place.name}! ${place.magicalStory}`
        : `Has seleccionado ${place.name}. ${place.historicalInfo}`;
    }
    
    addSystemMessage(message);
    onNavigate('chat');
  };

  /**
   * Renderiza la información detallada de un lugar
   */
  const renderPlaceDetails = (place) => {
    const isChild = userProfile.type === 'child';
    const isEnglish = userProfile.language === 'en';

    return (
      <Card className="mb-4">
        <CardContent>
          <div className="space-y-4">
            
            {/* Encabezado del lugar */}
            <div className="flex items-start gap-3">
              <MapPin 
                className="w-6 h-6 flex-shrink-0 mt-1"
                style={{ color: COLORS.SECONDARY_RED }} 
              />
              <div className="flex-1">
                <h3 
                  className="font-title font-bold text-xl mb-2"
                  style={{ color: COLORS.PRIMARY_BROWN }}
                >
                  {place.name}
                </h3>
                <p 
                  className="font-body text-sm mb-3"
                  style={{ color: COLORS.BLACK }}
                >
                  {place.description}
                </p>
                
                {/* Distancia si está disponible */}
                {place.distance && (
                  <div 
                    className="text-xs font-body"
                    style={{ color: COLORS.PRIMARY_BROWN }}
                  >
                    📍 {place.distance.toFixed(1)} km {userProfile.language === 'en' ? 'away' : 'de distancia'}
                  </div>
                )}
              </div>
            </div>

            {/* Historia mágica para niños */}
            {isChild && (
              <div 
                className="p-3 rounded-lg"
                style={{ backgroundColor: COLORS.SECONDARY_BLUE }}
              >
                <p 
                  className="text-sm font-bold font-body mb-1"
                  style={{ color: COLORS.WHITE }}
                >
                  🪄 {isEnglish ? 'Magical Story:' : 'Historia Mágica:'}
                </p>
                <p 
                  className="text-sm font-body"
                  style={{ color: COLORS.WHITE }}
                >
                  {place.magicalStory}
                </p>
              </div>
            )}

            {/* Información histórica para adultos */}
            {!isChild && (
              <div 
                className="p-3 rounded-lg"
                style={{ backgroundColor: COLORS.BACKGROUND }}
              >
                <p 
                  className="text-sm font-bold font-body mb-1"
                  style={{ color: COLORS.PRIMARY_BROWN }}
                >
                  📚 {isEnglish ? 'Historical Information:' : 'Información Histórica:'}
                </p>
                <p 
                  className="text-sm font-body"
                  style={{ color: COLORS.BLACK }}
                >
                  {place.historicalInfo}
                </p>
              </div>
            )}

            {/* Información práctica */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              
              {/* Horarios */}
              <div className="flex items-center gap-2">
                <Clock 
                  className="w-4 h-4"
                  style={{ color: COLORS.PRIMARY_BROWN }} 
                />
                <div>
                  <div 
                    className="font-bold font-body"
                    style={{ color: COLORS.PRIMARY_BROWN }}
                  >
                    {isEnglish ? 'Hours:' : 'Horarios:'}
                  </div>
                  <div 
                    className="font-body"
                    style={{ color: COLORS.BLACK }}
                  >
                    {place.openingHours}
                  </div>
                </div>
              </div>

              {/* Accesibilidad */}
              <div className="flex items-center gap-2">
                <Accessibility 
                  className="w-4 h-4"
                  style={{ color: COLORS.PRIMARY_BROWN }} 
                />
                <div>
                  <div 
                    className="font-bold font-body"
                    style={{ color: COLORS.PRIMARY_BROWN }}
                  >
                    {isEnglish ? 'Accessible:' : 'Accesible:'}
                  </div>
                  <div 
                    className="font-body"
                    style={{ color: COLORS.BLACK }}
                  >
                    {place.accessibility.wheelchair ? '✅' : '❌'}
                  </div>
                </div>
              </div>
            </div>

            {/* Actividad para niños */}
            {isChild && place.childActivity && (
              <div 
                className="p-3 rounded-lg"
                style={{ backgroundColor: COLORS.PRIMARY_YELLOW }}
              >
                <p 
                  className="text-sm font-bold font-body mb-1"
                  style={{ color: COLORS.BLACK }}
                >
                  🎮 {isEnglish ? 'Fun Activity:' : 'Actividad Divertida:'}
                </p>
                <p 
                  className="text-sm font-body"
                  style={{ color: COLORS.BLACK }}
                >
                  {place.childActivity}
                </p>
              </div>
            )}

            {/* Información para padres */}
            {!isChild && place.parentInfo && (
              <div 
                className="p-3 rounded-lg"
                style={{ backgroundColor: COLORS.PRIMARY_YELLOW }}
              >
                <p 
                  className="text-sm font-bold font-body mb-1"
                  style={{ color: COLORS.BLACK }}
                >
                  👨‍👩‍👧‍👦 {isEnglish ? 'Family Info:' : 'Info Familiar:'}
                </p>
                <p 
                  className="text-sm font-body"
                  style={{ color: COLORS.BLACK }}
                >
                  {place.parentInfo}
                </p>
              </div>
            )}

            {/* Botón para explorar */}
            <Button
              variant="primary"
              onClick={() => explorePlaceWithRatoncito(place)}
              className="w-full"
            >
              {isEnglish 
                ? 'Explore with the Tooth Mouse' 
                : 'Explorar con el Ratoncito'
              }
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div 
      className="min-h-screen"
      style={{ backgroundColor: COLORS.BACKGROUND }}
    >
      <div className="p-4">
        
        {/* Encabezado */}
        <h2 
          className="text-2xl font-bold font-title text-center mb-6"
          style={{ color: COLORS.PRIMARY_BROWN }}
        >
          {userProfile.language === 'en' 
            ? 'Magical Places in Madrid' 
            : 'Lugares Mágicos de Madrid'
          }
        </h2>
        
        {/* Filtros */}
        <div className="mb-6">
          <div className="flex gap-2 overflow-x-auto pb-2">
            {filters.map((filter) => {
              const IconComponent = filter.icon;
              return (
                <Button
                  key={filter.id}
                  variant={activeFilter === filter.id ? 'primary' : 'outline'}
                  onClick={() => handleFilter(filter.id)}
                  className="flex-shrink-0 flex items-center gap-2 text-sm"
                >
                  <IconComponent className="w-4 h-4" />
                  {filter.label}
                </Button>
              );
            })}
          </div>
        </div>

        <div className="max-w-md mx-auto space-y-4">
          
          {/* Lista de lugares */}
          {filteredPlaces.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <MapPin 
                  className="w-12 h-12 mx-auto mb-4 opacity-50"
                  style={{ color: COLORS.GRAY_MEDIUM }} 
                />
                <p 
                  className="font-body"
                  style={{ color: COLORS.GRAY_DARK }}
                >
                  {userProfile.language === 'en'
                    ? 'No places found with the current filter'
                    : 'No se encontraron lugares con el filtro actual'
                  }
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredPlaces.map((place) => (
              <div key={place.id}>
                {selectedPlace?.id === place.id ? (
                  <>
                    {renderPlaceDetails(place)}
                    <Button
                      variant="outline"
                      onClick={() => setSelectedPlace(null)}
                      className="w-full mb-4"
                    >
                      {userProfile.language === 'en' ? 'Show less' : 'Mostrar menos'}
                    </Button>
                  </>
                ) : (
                  <Card 
                    hoverable 
                    onClick={() => handlePlaceSelect(place)}
                    className="cursor-pointer"
                  >
                    <CardContent>
                      <div className="flex items-start gap-3">
                        <MapPin 
                          className="w-6 h-6 flex-shrink-0"
                          style={{ color: COLORS.SECONDARY_RED }} 
                        />
                        <div className="flex-1">
                          <h3 
                            className="font-title font-bold text-lg"
                            style={{ color: COLORS.PRIMARY_BROWN }}
                          >
                            {place.name}
                          </h3>
                          <p 
                            className="text-sm font-body mb-2"
                            style={{ color: COLORS.BLACK }}
                          >
                            {place.description}
                          </p>
                          
                          {/* Distancia */}
                          {place.distance && (
                            <div 
                              className="text-xs font-body"
                              style={{ color: COLORS.PRIMARY_BROWN }}
                            >
                              📍 {place.distance.toFixed(1)} km
                            </div>
                          )}
                          
                          {/* Vista previa para niños */}
                          {userProfile.type === 'child' && (
                            <div 
                              className="text-xs font-body mt-2 p-2 rounded"
                              style={{ 
                                backgroundColor: COLORS.SECONDARY_BLUE + '20',
                                color: COLORS.PRIMARY_BROWN 
                              }}
                            >
                              🪄 {place.magicalStory.substring(0, 80)}...
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default MapPage;

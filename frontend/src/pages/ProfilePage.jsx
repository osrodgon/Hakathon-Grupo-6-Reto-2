import React from 'react';
import { Sparkles, Heart, User } from 'lucide-react';
import Button from '../components/common/Button';
import Card, { CardTitle, CardContent } from '../components/common/Card';
import { COLORS, FONTS } from '../config/constants';
import app4 from '../images/app4.png';

/**
 * Página de configuración del perfil de usuario
 * Permite personalizar la experiencia según tipo de usuario, idioma y accesibilidad
 * @param {Object} props
 * @param {Object} props.userProfile - Perfil actual del usuario
 * @param {function} props.updateProfile - Función para actualizar el perfil
 * @param {function} props.onComplete - Función para completar configuración
 */
const ProfilePage = ({ userProfile, updateProfile, onComplete }) => {

  /**
   * Maneja la selección del tipo de usuario
   * @param {string} type - 'child' o 'parent'
   */
  const handleUserTypeSelection = (type) => {
    updateProfile({ type });
  };

  /**
   * Maneja la selección del idioma
   * @param {string} language - 'es' o 'en'
   */
  const handleLanguageSelection = (language) => {
    updateProfile({ language });
  };

  /**
   * Maneja la selección de opciones de accesibilidad
   * @param {string} accessibility - Tipo de adaptación necesaria
   */
  const handleAccessibilityChange = (accessibility) => {
    updateProfile({ accessibility });
  };
  /**
   * Completa la configuración del perfil
   */
  const handleComplete = () => {
    if (userProfile.isFirstTime) {
      updateProfile({ isFirstTime: false });
    }
    onComplete();
  };

  return (
    <div 
      className="min-h-screen p-6"
      style={{ backgroundColor: COLORS.BACKGROUND }}
    >
      <div className="max-w-md mx-auto">
          {/* Encabezado de bienvenida */}
        <div className="text-center mb-8">
          <div className="animate-bounce-soft mb-4">
            <img 
              src={app4} 
              alt="Perfil Aventurero" 
              className="w-40 h-40 mx-auto object-contain"
            />
          </div>
          
          <h1 
            className="text-3xl font-bold font-title mb-2"
            style={{ color: COLORS.PRIMARY_BROWN }}
          >
            {userProfile.language === 'en' ? '¡Hello Adventurer!' : '¡Hola Aventurero!'}
          </h1>
          
          <p 
            className="font-body text-lg"
            style={{ color: COLORS.BLACK }}
          >
            {userProfile.language === 'en' 
              ? 'Tell me about yourself to personalize your adventure'
              : 'Cuéntame sobre ti para personalizar tu aventura'
            }
          </p>
        </div>

        <div className="space-y-6">
          
          {/* Selección de tipo de usuario */}
          <Card>
            <CardTitle size="md">
              {userProfile.language === 'en' ? 'Who are you?' : '¿Quién eres?'}
            </CardTitle>
            
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                
                {/* Opción Niño/a */}
                <Button
                  variant={userProfile.type === 'child' ? 'primary' : 'outline'}
                  onClick={() => handleUserTypeSelection('child')}
                  className="h-24 flex-col gap-2"
                >
                  <Heart 
                    className="w-8 h-8"
                    style={{ color: COLORS.SECONDARY_RED }} 
                  />
                  <span className="text-sm font-semibold">
                    {userProfile.language === 'en' ? 'Child' : 'Niño/a'}
                  </span>
                </Button>

                {/* Opción Padre/Madre */}
                <Button
                  variant={userProfile.type === 'parent' ? 'primary' : 'outline'}
                  onClick={() => handleUserTypeSelection('parent')}
                  className="h-24 flex-col gap-2"
                >
                  <User 
                    className="w-8 h-8"
                    style={{ color: COLORS.SECONDARY_BLUE }} 
                  />
                  <span className="text-sm font-semibold">
                    {userProfile.language === 'en' ? 'Parent' : 'Padre/Madre'}
                  </span>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Selección de idioma */}
          <Card>
            <CardTitle size="md">
              {userProfile.language === 'en' ? 'Preferred Language' : 'Idioma preferido'}
            </CardTitle>
            
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                
                <Button
                  variant={userProfile.language === 'es' ? 'primary' : 'outline'}
                  onClick={() => handleLanguageSelection('es')}
                  className="flex items-center justify-center gap-2"
                >
                  <span>Español 🇪🇸</span>
                </Button>

                <Button
                  variant={userProfile.language === 'en' ? 'primary' : 'outline'}
                  onClick={() => handleLanguageSelection('en')}
                  className="flex items-center justify-center gap-2"
                >
                  <span>English 🇬🇧</span>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Opciones de accesibilidad */}
          <Card>
            <CardTitle size="md">
              {userProfile.language === 'en' 
                ? 'Do you need any adaptation?' 
                : '¿Necesitas alguna adaptación?'
              }
            </CardTitle>
            
            <CardContent>
              <select
                value={userProfile.accessibility}
                onChange={(e) => handleAccessibilityChange(e.target.value)}
                className="w-full p-3 rounded-lg border-2 font-body"
                style={{ 
                  backgroundColor: COLORS.WHITE,
                  borderColor: COLORS.GRAY_MEDIUM,
                  color: COLORS.BLACK 
                }}
              >
                <option value="none">
                  {userProfile.language === 'en' 
                    ? 'No special adaptations' 
                    : 'Sin adaptaciones especiales'
                  }
                </option>
                <option value="visual">
                  {userProfile.language === 'en' 
                    ? 'Visual adaptation' 
                    : 'Adaptación visual'
                  }
                </option>
                <option value="hearing">
                  {userProfile.language === 'en' 
                    ? 'Hearing adaptation' 
                    : 'Adaptación auditiva'
                  }
                </option>
                <option value="mobility">
                  {userProfile.language === 'en' 
                    ? 'Mobility adaptation' 
                    : 'Adaptación de movilidad'
                  }
                </option>
              </select>
            </CardContent>
          </Card>

          {/* Información adicional para niños */}
          {userProfile.type === 'child' && (
            <Card>
              <CardContent>
                <div 
                  className="p-4 rounded-lg text-center"
                  style={{ backgroundColor: COLORS.SECONDARY_BLUE }}
                >
                  <p 
                    className="font-body font-semibold text-sm"
                    style={{ color: COLORS.WHITE }}
                  >
                    {userProfile.language === 'en'
                      ? '🎮 Get ready for magical games and incredible stories!'
                      : '🎮 ¡Prepárate para juegos mágicos e historias increíbles!'
                    }
                  </p>
                </div>
              </CardContent>
            </Card>
          )}          {/* Botones para continuar */}
          <div className="space-y-3">
            <Button
              variant="primary"
              size="lg"
              onClick={handleComplete}
              className="w-full"
            >
              {userProfile.isFirstTime 
                ? (userProfile.language === 'en' ? '✨ Start Adventure!' : '✨ ¡Comenzar Aventura!')
                : (userProfile.language === 'en' ? '💾 Save Changes' : '💾 Guardar Cambios')
              }
            </Button>
            
            {/* Botón volver solo si no es primera vez */}
            {!userProfile.isFirstTime && (
              <Button
                variant="outline"
                size="lg"
                onClick={onComplete}
                className="w-full"
              >
                {userProfile.language === 'en' ? '← Back' : '← Volver'}
              </Button>
            )}
          </div>

          {/* Información de privacidad */}
          <div className="text-center">
            <p 
              className="text-xs font-body opacity-75"
              style={{ color: COLORS.PRIMARY_BROWN }}
            >
              {userProfile.language === 'en'
                ? 'Your preferences are saved locally on your device'
                : 'Tus preferencias se guardan localmente en tu dispositivo'
              }
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;

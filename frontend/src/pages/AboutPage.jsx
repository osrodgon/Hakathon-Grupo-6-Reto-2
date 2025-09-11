import React from 'react';
import { Star, Heart, Users, Crown, Gift, Sparkles } from 'lucide-react';
import Card, { CardTitle, CardContent } from '../components/common/Card';
import Button from '../components/common/Button';
import { COLORS } from '../config/constants';

/**
 * Página "Sobre Nosotros" con información del proyecto y equipo
 * @param {Object} props
 * @param {Object} props.userProfile - Perfil del usuario
 * @param {function} props.onNavigate - Función de navegación
 */
const AboutPage = ({ userProfile, onNavigate }) => {
  
  /**
   * Información del equipo de desarrollo
   */
  const teamMembers = [
    {
      name: "Equipo Madrid Mágico",
      role: userProfile.language === 'en' ? "Developers & Storytellers" : "Desarrolladores y Narradores",
      description: userProfile.language === 'en' 
        ? "Passionate about creating magical experiences that combine culture and fun"
        : "Apasionados por crear experiencias mágicas que combinan cultura y diversión",
      icon: Heart
    },
    {
      name: "Ratoncito Pérez",
      role: userProfile.language === 'en' ? "Chief Magical Officer" : "Director de Magia",
      description: userProfile.language === 'en'
        ? "Our beloved virtual guide who brings Madrid to life with incredible stories"
        : "Nuestro querido guía virtual que hace que Madrid cobre vida con historias increíbles",
      icon: Crown
    }
  ];

  /**
   * Características principales de la aplicación
   */
  const features = [
    {
      icon: Sparkles,
      title: userProfile.language === 'en' ? "Magical Stories" : "Historias Mágicas",
      description: userProfile.language === 'en'
        ? "Each place in Madrid has a special story adapted for children"
        : "Cada lugar de Madrid tiene una historia especial adaptada para niños"
    },
    {
      icon: Users,
      title: userProfile.language === 'en' ? "Family Experience" : "Experiencia Familiar",
      description: userProfile.language === 'en'
        ? "Content adapted for both children and adults with different approaches"
        : "Contenido adaptado tanto para niños como adultos con enfoques diferentes"
    },
    {
      icon: Gift,
      title: userProfile.language === 'en' ? "Interactive Learning" : "Aprendizaje Interactivo",
      description: userProfile.language === 'en'
        ? "Games and activities that make learning about Madrid fun and memorable"
        : "Juegos y actividades que hacen que aprender sobre Madrid sea divertido y memorable"
    }
  ];

  return (
    <div 
      className="min-h-screen p-6"
      style={{ backgroundColor: COLORS.BACKGROUND }}
    >
      <div className="max-w-md mx-auto space-y-6">
        
        {/* Encabezado */}
        <div className="text-center mb-8">
          <div className="animate-bounce-soft mb-4">
            <Star 
              className="w-16 h-16 mx-auto"
              style={{ color: COLORS.PRIMARY_BROWN }} 
            />
          </div>
          <h1 
            className="text-3xl font-bold font-title"
            style={{ color: COLORS.PRIMARY_BROWN }}
          >
            {userProfile.language === 'en' ? 'About Us' : 'Sobre Nosotros'}
          </h1>
        </div>

        {/* Misión del proyecto */}
        <Card>
          <CardTitle>
            {userProfile.language === 'en' ? 'Our Mission' : 'Nuestra Misión'}
          </CardTitle>
          <CardContent>
            <p 
              className="font-body leading-relaxed"
              style={{ color: COLORS.BLACK }}
            >
              {userProfile.language === 'en'
                ? "We are a passionate team dedicated to creating magical experiences that combine Madrid's rich culture and history with fantasy and fun for the whole family. Our goal is to make every visit to Madrid an unforgettable adventure."
                : "Somos un equipo apasionado por crear experiencias mágicas que combinan la rica cultura e historia de Madrid con la fantasía y diversión para toda la familia. Nuestro objetivo es hacer que cada visita a Madrid sea una aventura inolvidable."
              }
            </p>
          </CardContent>
        </Card>

        {/* Características principales */}
        <Card>
          <CardTitle>
            {userProfile.language === 'en' ? 'What Makes Us Special' : 'Qué nos hace especiales'}
          </CardTitle>
          <CardContent>
            <div className="space-y-4">
              {features.map((feature, index) => {
                const IconComponent = feature.icon;
                return (
                  <div key={index} className="flex items-start gap-3">
                    <div 
                      className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
                      style={{ backgroundColor: COLORS.PRIMARY_YELLOW }}
                    >
                      <IconComponent 
                        className="w-5 h-5"
                        style={{ color: COLORS.PRIMARY_BROWN }} 
                      />
                    </div>
                    <div>
                      <h3 
                        className="font-title font-bold text-sm mb-1"
                        style={{ color: COLORS.PRIMARY_BROWN }}
                      >
                        {feature.title}
                      </h3>
                      <p 
                        className="font-body text-sm"
                        style={{ color: COLORS.BLACK }}
                      >
                        {feature.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Equipo */}
        <Card>
          <CardTitle>
            {userProfile.language === 'en' ? 'Our Team' : 'Nuestro Equipo'}
          </CardTitle>
          <CardContent>
            <div className="space-y-4">
              {teamMembers.map((member, index) => {
                const IconComponent = member.icon;
                return (
                  <div 
                    key={index}
                    className="p-4 rounded-lg"
                    style={{ backgroundColor: COLORS.BACKGROUND }}
                  >
                    <div className="flex items-start gap-3">
                      <div 
                        className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0"
                        style={{ backgroundColor: COLORS.SECONDARY_BLUE }}
                      >
                        <IconComponent 
                          className="w-6 h-6"
                          style={{ color: COLORS.WHITE }} 
                        />
                      </div>
                      <div>
                        <h3 
                          className="font-title font-bold text-lg"
                          style={{ color: COLORS.PRIMARY_BROWN }}
                        >
                          {member.name}
                        </h3>
                        <p 
                          className="font-body text-sm font-semibold mb-2"
                          style={{ color: COLORS.SECONDARY_BLUE }}
                        >
                          {member.role}
                        </p>
                        <p 
                          className="font-body text-sm"
                          style={{ color: COLORS.BLACK }}
                        >
                          {member.description}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Agradecimientos especiales */}
        <Card>
          <CardContent>
            <div 
              className="p-4 rounded-lg text-center"
              style={{ backgroundColor: COLORS.SECONDARY_BLUE }}
            >
              <Crown 
                className="w-8 h-8 mx-auto mb-3"
                style={{ color: COLORS.WHITE }} 
              />
              <h3 
                className="font-title font-bold text-lg mb-2"
                style={{ color: COLORS.WHITE }}
              >
                {userProfile.language === 'en' 
                  ? 'Special Thanks' 
                  : 'Agradecimientos Especiales'
                }
              </h3>
              <p 
                className="font-body text-sm"
                style={{ color: COLORS.WHITE }}
              >
                {userProfile.language === 'en'
                  ? "To all the families who inspire us to create magical experiences and to Madrid, the city that makes everything possible."
                  : "A todas las familias que nos inspiran a crear experiencias mágicas y a Madrid, la ciudad que hace todo posible."
                }
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Mensaje final con el Ratoncito */}
        <Card>
          <CardContent>
            <div 
              className="p-4 rounded-lg text-center"
              style={{ backgroundColor: COLORS.PRIMARY_YELLOW }}
            >
              <div className="flex items-center justify-center gap-2 mb-3">
                <Crown 
                  className="w-6 h-6"
                  style={{ color: COLORS.PRIMARY_BROWN }} 
                />
                <h4 
                  className="font-title font-bold"
                  style={{ color: COLORS.PRIMARY_BROWN }}
                >
                  {userProfile.language === 'en' ? 'Message from the Tooth Mouse' : 'Mensaje del Ratoncito Pérez'}
                </h4>
              </div>
              <p 
                className="font-body text-sm mb-4"
                style={{ color: COLORS.BLACK }}
              >
                {userProfile.language === 'en'
                  ? "\"Thank you for joining me on this magical adventure through Madrid! Remember, magic is everywhere if you know how to look for it. Keep exploring and dreaming!\""
                  : "\"¡Gracias por acompañarme en esta aventura mágica por Madrid! Recuerda, la magia está en todas partes si sabes cómo buscarla. ¡Sigue explorando y soñando!\""
                }
              </p>
              
              {/* Elementos decorativos */}
              <div className="flex justify-center space-x-2">
                <Sparkles 
                  className="w-4 h-4 animate-pulse-glow"
                  style={{ color: COLORS.SECONDARY_RED }} 
                />
                <Heart 
                  className="w-4 h-4 animate-bounce-soft"
                  style={{ color: COLORS.SECONDARY_RED }} 
                />
                <Sparkles 
                  className="w-4 h-4 animate-pulse-glow"
                  style={{ color: COLORS.SECONDARY_RED }} 
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Botones de acción */}
        <div className="space-y-3">
          <Button
            variant="primary"
            onClick={() => onNavigate('home')}
            className="w-full"
          >
            {userProfile.language === 'en' ? 'Back to Adventure' : 'Volver a la Aventura'}
          </Button>
          
          <Button
            variant="outline"
            onClick={() => onNavigate('chat')}
            className="w-full"
          >
            {userProfile.language === 'en' ? 'Chat with Tooth Mouse' : 'Chatear con el Ratoncito'}
          </Button>
        </div>

        {/* Información de versión */}
        <div className="text-center">
          <p 
            className="text-xs font-body opacity-75"
            style={{ color: COLORS.PRIMARY_BROWN }}
          >
            {userProfile.language === 'en' 
              ? 'Ratoncito Pérez Madrid App v1.0' 
              : 'App Ratoncito Pérez Madrid v1.0'
            }
          </p>
          <p 
            className="text-xs font-body opacity-50 mt-1"
            style={{ color: COLORS.PRIMARY_BROWN }}
          >
            {userProfile.language === 'en' 
              ? 'Made with ❤️ for families visiting Madrid' 
              : 'Hecho con ❤️ para familias visitando Madrid'
            }
          </p>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;

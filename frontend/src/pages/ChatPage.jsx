import React, { useEffect } from 'react';
import { Send, Crown } from 'lucide-react';
import Button from '../components/common/Button';
import Card, { CardContent } from '../components/common/Card';
import { COLORS } from '../config/constants';
import { formatTime } from '../utils/dateUtils';

/**
 * Página de chat interactivo con el Ratoncito Pérez
 * @param {Object} props
 * @param {Object} props.userProfile - Perfil del usuario
 * @param {Object} props.chatData - Datos del chat (history, currentMessage, etc.)
 * @param {function} props.setChatData - Función para actualizar datos del chat
 * @param {function} props.sendMessage - Función para enviar mensajes
 * @param {Object} props.chatEndRef - Referencia para scroll automático
 */
const ChatPage = ({ 
  userProfile, 
  chatData, 
  setChatData, 
  sendMessage, 
  chatEndRef,
  isTyping 
}) => {

  // Añadir mensaje de bienvenida si el chat está vacío
  useEffect(() => {
    if (chatData.chatHistory.length === 0) {
      const welcomeMessage = getWelcomeMessage();
      setChatData(prev => ({
        ...prev,
        chatHistory: [{
          type: 'ratoncito',
          content: welcomeMessage,
          timestamp: new Date(),
          id: Date.now()
        }]
      }));
    }
  }, []);

  /**
   * Genera mensaje de bienvenida personalizado
   */
  const getWelcomeMessage = () => {
    const isChild = userProfile.type === 'child';
    const isEnglish = userProfile.language === 'en';
    
    if (isEnglish) {
      return isChild
        ? "Hello little adventurer! 🐭✨ I'm the Tooth Mouse and I'm here to show you the magical secrets of Madrid. What would you like to discover first?"
        : "Hello! I'm here to enrich your family visit to Madrid with fascinating cultural information and stories. How can I help you today?";
    }
    
    return isChild
      ? "¡Hola pequeño aventurero! 🐭✨ Soy el Ratoncito Pérez y estoy aquí para mostrarte los secretos mágicos de Madrid. ¿Qué te gustaría descubrir primero?"
      : "¡Hola! Estoy aquí para enriquecer su visita familiar a Madrid con información cultural e historias fascinantes. ¿En qué puedo ayudarles hoy?";
  };

  /**
   * Maneja el envío de mensajes
   */
  const handleSendMessage = () => {
    if (chatData.currentMessage.trim()) {
      sendMessage();
    }
  };

  /**
   * Maneja la tecla Enter para enviar mensajes
   */
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  /**
   * Renderiza un mensaje individual
   */
  const renderMessage = (message, index) => {
    const isUser = message.type === 'user';
    const isSystem = message.type === 'system';
    
    return (
      <div 
        key={message.id || index} 
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div 
          className={`
            max-w-xs lg:max-w-md px-4 py-3 rounded-lg font-body
            ${isUser ? 'rounded-br-none' : 'rounded-bl-none'}
            ${isSystem ? 'max-w-full' : ''}
          `}
          style={{
            backgroundColor: isUser 
              ? COLORS.SECONDARY_BLUE 
              : isSystem 
                ? COLORS.BACKGROUND 
                : COLORS.PRIMARY_YELLOW,
            color: isUser 
              ? COLORS.WHITE 
              : COLORS.BLACK,
            border: isSystem ? `1px solid ${COLORS.GRAY_LIGHT}` : 'none'
          }}
        >
          {/* Contenido del mensaje */}
          <div className="text-sm leading-relaxed">
            {message.content}
          </div>
          
          {/* Timestamp */}
          <div 
            className="text-xs mt-2 opacity-75"
            style={{ 
              color: isUser ? COLORS.WHITE : COLORS.PRIMARY_BROWN 
            }}
          >
            {formatTime(message.timestamp)}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div 
      className="min-h-screen flex flex-col"
      style={{ backgroundColor: COLORS.BACKGROUND }}
    >
      
      {/* Encabezado del chat */}
      <div 
        className="sticky top-0 z-10 p-4 border-b"
        style={{ 
          backgroundColor: COLORS.WHITE,
          borderColor: COLORS.GRAY_LIGHT 
        }}
      >
        <div className="max-w-md mx-auto">
          <div className="flex items-center gap-3">
            <div 
              className="w-12 h-12 rounded-full flex items-center justify-center"
              style={{ backgroundColor: COLORS.PRIMARY_YELLOW }}
            >
              <Crown 
                className="w-6 h-6"
                style={{ color: COLORS.PRIMARY_BROWN }} 
              />
            </div>
            <div>
              <h2 
                className="font-title font-bold text-lg"
                style={{ color: COLORS.PRIMARY_BROWN }}
              >
                {userProfile.language === 'en' ? 'Tooth Mouse' : 'Ratoncito Pérez'}
              </h2>
              <p 
                className="text-sm font-body opacity-75"
                style={{ color: COLORS.BLACK }}
              >
                {userProfile.language === 'en' 
                  ? 'Your magical guide in Madrid' 
                  : 'Tu guía mágico en Madrid'
                }
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Área de mensajes */}
      <div className="flex-1 overflow-y-auto p-4 pb-24">
        <div className="max-w-md mx-auto">
          
          {/* Mensaje de bienvenida si no hay historial */}
          {chatData.chatHistory.length === 0 && (
            <Card className="mb-6">
              <CardContent className="text-center py-6">
                <Crown 
                  className="w-12 h-12 mx-auto mb-3"
                  style={{ color: COLORS.PRIMARY_BROWN }} 
                />
                <h3 
                  className="font-title font-bold text-lg mb-2"
                  style={{ color: COLORS.PRIMARY_BROWN }}
                >
                  {userProfile.language === 'en' 
                    ? 'Hello! I\'m the Tooth Mouse' 
                    : '¡Hola! Soy el Ratoncito Pérez'
                  }
                </h3>
                <p 
                  className="font-body text-sm"
                  style={{ color: COLORS.BLACK }}
                >
                  {userProfile.language === 'en'
                    ? "Ready for a magical adventure? Ask me anything!"
                    : "¿Estás listo para una aventura mágica? ¡Pregúntame lo que quieras!"
                  }
                </p>
              </CardContent>
            </Card>
          )}

          {/* Historial de mensajes */}
          {chatData.chatHistory.map((message, index) => 
            renderMessage(message, index)
          )}

          {/* Indicador de que el Ratoncito está escribiendo */}
          {isTyping && (
            <div className="flex justify-start mb-4">
              <div 
                className="max-w-xs px-4 py-3 rounded-lg rounded-bl-none"
                style={{ backgroundColor: COLORS.PRIMARY_YELLOW }}
              >
                <div className="flex items-center gap-1">
                  <span 
                    className="font-body text-sm"
                    style={{ color: COLORS.BLACK }}
                  >
                    {userProfile.language === 'en' 
                      ? 'Tooth Mouse is typing' 
                      : 'Ratoncito Pérez está escribiendo'
                    }
                  </span>
                  <div className="flex gap-1 ml-2">
                    <div 
                      className="w-2 h-2 rounded-full animate-bounce"
                      style={{ 
                        backgroundColor: COLORS.PRIMARY_BROWN,
                        animationDelay: '0ms'
                      }}
                    />
                    <div 
                      className="w-2 h-2 rounded-full animate-bounce"
                      style={{ 
                        backgroundColor: COLORS.PRIMARY_BROWN,
                        animationDelay: '200ms'
                      }}
                    />
                    <div 
                      className="w-2 h-2 rounded-full animate-bounce"
                      style={{ 
                        backgroundColor: COLORS.PRIMARY_BROWN,
                        animationDelay: '400ms'
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Referencia para scroll automático */}
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Input del chat - Fijo en la parte inferior */}
      <div 
        className="fixed bottom-0 left-0 right-0 p-4 border-t"
        style={{ 
          backgroundColor: COLORS.WHITE,
          borderColor: COLORS.GRAY_LIGHT 
        }}
      >
        <div className="max-w-md mx-auto">
          <div className="flex gap-2">
            <input
              type="text"
              value={chatData.currentMessage}
              onChange={(e) => setChatData(prev => ({
                ...prev,
                currentMessage: e.target.value
              }))}
              onKeyPress={handleKeyPress}
              placeholder={userProfile.language === 'en' 
                ? "What do you want to know? 🐭" 
                : "¿Qué quieres saber? 🐭"
              }
              className="flex-1 p-3 rounded-lg border-2 font-body focus:outline-none focus:ring-2 focus:ring-offset-1"
              style={{ 
                backgroundColor: COLORS.BACKGROUND,
                borderColor: COLORS.PRIMARY_YELLOW,
                color: COLORS.BLACK
              }}
              disabled={isTyping}
            />
            
            <Button
              variant="secondary"
              onClick={handleSendMessage}
              disabled={!chatData.currentMessage.trim() || isTyping}
              className="px-4"
            >
              <Send className="w-5 h-5" />
            </Button>
          </div>

          {/* Sugerencias de preguntas para niños */}
          {userProfile.type === 'child' && chatData.chatHistory.length <= 1 && (
            <div className="mt-3">
              <div className="flex gap-2 overflow-x-auto pb-2">
                {[
                  userProfile.language === 'en' ? "Tell me a story!" : "¡Cuéntame una historia!",
                  userProfile.language === 'en' ? "Where are the treasures?" : "¿Dónde están los tesoros?",
                  userProfile.language === 'en' ? "Let's play!" : "¡Vamos a jugar!"
                ].map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => setChatData(prev => ({
                      ...prev,
                      currentMessage: suggestion
                    }))}
                    className="flex-shrink-0 px-3 py-2 rounded-full text-xs font-body border-2 hover:scale-105 transition-transform"
                    style={{
                      backgroundColor: COLORS.BACKGROUND,
                      borderColor: COLORS.PRIMARY_YELLOW,
                      color: COLORS.BLACK
                    }}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatPage;

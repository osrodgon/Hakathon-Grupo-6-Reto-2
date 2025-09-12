import React, { useEffect, useState, useRef } from 'react';
import { Send, Crown, Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import Button from '../components/common/Button';
import Card, { CardContent } from '../components/common/Card';
import { COLORS } from '../config/constants';
import { formatTime } from '../utils/dateUtils';
import { getCurrentLocation } from '../utils/locationUtils';

/**
 * Página de chat interactivo con el Ratoncito Pérez
 */
const ChatPage = ({ 
  userProfile, 
  chatData, 
  setChatData, 
  chatEndRef,
  isTyping 
}) => {

  // Estado local para manejar la carga
  const [isLoading, setIsLoading] = useState(false);

  // Estado para el reconocimiento de voz
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const recognitionRef = useRef(null);

  // Estado para síntesis de voz (text-to-speech)
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechSynthesisSupported, setSpeechSynthesisSupported] = useState(false);
  const speechSynthesisRef = useRef(null);

  // Configuración del backend API
  const BACKEND_URL = 'http://127.0.0.1:8000';
  const USE_MOCK_BACKEND = false;

  /**
   * Función mock para simular respuestas del backend durante desarrollo
   */
  const mockBackendResponse = async (query) => {
    const response = `¡Hola! Recibí tu mensaje: "${query}". Soy el Ratoncito Pérez 🐭✨`;
    await new Promise(resolve => setTimeout(resolve, 500));
    return response;
  };

  /**
   * Inicializa el reconocimiento de voz y síntesis de voz
   */
  useEffect(() => {
    // Verificar si el navegador soporta Web Speech API
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      setSpeechSupported(true);
      
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      // Configuración del reconocimiento
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = userProfile.language === 'en' ? 'en-US' : 'es-ES';
      
      // Eventos del reconocimiento
      recognition.onstart = () => {
        setIsListening(true);
        console.log('🎤 Reconocimiento de voz iniciado');
      };
      
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log('🗣️ Texto reconocido:', transcript);
        
        setChatData(prev => ({
          ...prev,
          currentMessage: transcript
        }));
      };
      
      recognition.onerror = (event) => {
        console.error('❌ Error en reconocimiento de voz:', event.error);
        setIsListening(false);
      };
      
      recognition.onend = () => {
        setIsListening(false);
        console.log('🎤 Reconocimiento de voz finalizado');
      };
      
      recognitionRef.current = recognition;
    } else {
      console.log('⚠️ Reconocimiento de voz no soportado en este navegador');
      setSpeechSupported(false);
    }

    // Verificar si el navegador soporta Speech Synthesis
    if ('speechSynthesis' in window) {
      setSpeechSynthesisSupported(true);
      speechSynthesisRef.current = window.speechSynthesis;
      console.log('🔊 Síntesis de voz disponible');
    } else {
      console.log('⚠️ Síntesis de voz no soportada en este navegador');
      setSpeechSynthesisSupported(false);
    }
    
    // Cleanup
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (speechSynthesisRef.current) {
        speechSynthesisRef.current.cancel();
      }
    };
  }, [userProfile.language]);

  /**
   * Inicia o detiene el reconocimiento de voz
   */
  const toggleSpeechRecognition = () => {
    if (!speechSupported || !recognitionRef.current) {
      alert(userProfile.language === 'en' 
        ? 'Voice recognition is not supported in your browser'
        : 'El reconocimiento de voz no está soportado en tu navegador'
      );
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      try {
        recognitionRef.current.start();
      } catch (error) {
        console.error('Error al iniciar reconocimiento:', error);
        setIsListening(false);
      }
    }
  };

  /**
   * Función para limpiar texto antes de la síntesis de voz
   */
  const cleanTextForSpeech = (text) => {
    if (!text) return '';
    
    return text
      // Remover encabezados markdown (# ## ### etc.)
      .replace(/^#{1,6}\s+/gm, '')
      // Remover markdown bold y cursiva
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/__(.*?)__/g, '$1')
      .replace(/_(.*?)_/g, '$1')
      // Remover listas markdown
      .replace(/^\s*[-*+]\s+/gm, '')
      .replace(/^\s*\d+\.\s+/gm, '')
      // Remover enlaces markdown [texto](url)
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
      // Remover código inline `código`
      .replace(/`([^`]+)`/g, '$1')
      // Remover bloques de código ```
      .replace(/```[\s\S]*?```/g, '')
      // Remover caracteres especiales de markdown
      .replace(/[#*_`~\[\](){}|\\]/g, '')
      // Remover guiones largos y caracteres especiales
      .replace(/[-—–]/g, ' ')
      // Remover emojis comunes
      .replace(/🐭|✨|🎮|💡|🔍|🎭|🌟|📚|🏛️|🚶‍♂️|🎨|🏆|🎤|🔊|⚠️|❌|🗣️|🌤️|☀️|🌧️|❄️|🌈/g, '')
      // Remover saltos de línea múltiples y reemplazar con espacios
      .replace(/\n+/g, ' ')
      // Remover espacios múltiples
      .replace(/\s+/g, ' ')
      // Remover puntos suspensivos múltiples
      .replace(/\.{2,}/g, '.')
      // Remover caracteres especiales adicionales
      .replace(/[^\w\s.,;:!?¿¡áéíóúñüÁÉÍÓÚÑÜ]/g, ' ')
      // Limpiar espacios al inicio y final
      .trim();
  };

  /**
   * Lee en voz alta la última respuesta del Ratoncito Pérez
   */
  const speakLastResponse = () => {
    if (!speechSynthesisSupported || !speechSynthesisRef.current) {
      alert(userProfile.language === 'en' 
        ? 'Text-to-speech is not supported in your browser'
        : 'La síntesis de voz no está soportada en tu navegador'
      );
      return;
    }

    // Detener cualquier síntesis en curso
    if (isSpeaking) {
      speechSynthesisRef.current.cancel();
      setIsSpeaking(false);
      return;
    }

    // Buscar la última respuesta del ratoncito
    const lastRatoncitoMessage = [...chatData.chatHistory]
      .reverse()
      .find(msg => msg.type === 'ratoncito');

    if (!lastRatoncitoMessage) {
      console.log('No hay mensajes del ratoncito para leer');
      return;
    }

    const textToSpeak = cleanTextForSpeech(lastRatoncitoMessage.content);
    
    if (!textToSpeak) {
      console.log('No hay texto válido para leer');
      return;
    }

    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    
    // Configurar la voz según el idioma
    utterance.lang = userProfile.language === 'en' ? 'en-US' : 'es-ES';
    utterance.rate = 0.9; // Velocidad ligeramente más lenta para mayor claridad
    utterance.pitch = 1.1; // Tono ligeramente más alto para sonar más amigable
    utterance.volume = 0.8;

    // Eventos de la síntesis
    utterance.onstart = () => {
      setIsSpeaking(true);
      console.log('🔊 Iniciando síntesis de voz');
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      console.log('🔊 Síntesis de voz completada');
    };

    utterance.onerror = (event) => {
      console.error('❌ Error en síntesis de voz:', event.error);
      setIsSpeaking(false);
    };

    // Intentar seleccionar una voz apropiada
    const voices = speechSynthesisRef.current.getVoices();
    const preferredVoice = voices.find(voice => 
      voice.lang.startsWith(userProfile.language === 'en' ? 'en' : 'es')
    );
    
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    speechSynthesisRef.current.speak(utterance);
  };

  /**
   * Función para llamar al endpoint /guide del backend
   */
  const callBackendGuide = async (query) => {
    const location = await getCurrentLocation();
    try {
      console.log('=== LLAMADA AL BACKEND ===');
      console.log('Query:', query);
      
      if (USE_MOCK_BACKEND) {
        return await mockBackendResponse(query);
      }
      
      const payload = {
        query: String(query),
        lat: location.lat,
        lon: location.lon,
        radio_km: 0.5,
        categoria: 'museo',
        adulto: Boolean(userProfile.type === 'parent'),
        infantil: Boolean(userProfile.type === 'child'),
        accesibilidad: Boolean(userProfile.accessibility && userProfile.accessibility !== 'none')
      };

      const response = await fetch(`${BACKEND_URL}/guide`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        console.log('Backend error, usando mock response');
        return await mockBackendResponse(query);
      }

      const response_data = await response.json();
      console.log('Respuesta del backend:', response_data);
      
      // Extraer data.guide.raw (donde está el contenido real)
      if (response_data.data && response_data.data.guide && response_data.data.guide.raw) {
        let content = response_data.data.guide.raw;
        if (content.startsWith('```markdown\n')) {
          content = content.replace(/^```markdown\n/, '').replace(/\n```$/, '');
        }
        return content;
      } else if (response_data.data && response_data.data.guide) {
        return JSON.stringify(response_data.data.guide);
      } else if (response_data.guide && response_data.guide.raw) {
        let content = response_data.guide.raw;
        if (content.startsWith('```markdown\n')) {
          content = content.replace(/^```markdown\n/, '').replace(/\n```$/, '');
        }
        return content;
      } else {
        return "No se pudo obtener la respuesta del servidor.";
      }
      
    } catch (error) {
      console.error('Error en backend:', error);
      
      if (!USE_MOCK_BACKEND) {
        try {
          return await mockBackendResponse(query);
        } catch (mockError) {
          console.error('Mock response también falló:', mockError);
        }
      }
      
      const errorMessage = userProfile.language === 'en' 
        ? "I'm sorry, I'm having trouble connecting right now. Please try again in a moment! 🐭✨"
        : "Lo siento, tengo problemas para conectarme ahora. ¡Inténtalo de nuevo en un momento! 🐭✨";
        
      return errorMessage;
    }
  };

  // La función getWelcomeMessage está en el hook useChat

  // El mensaje de bienvenida se maneja desde App.jsx mediante useChat

  // Scroll automático
  useEffect(() => {
    if (chatEndRef?.current) {
      setTimeout(() => {
        chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  }, [chatData.chatHistory]);

  /**
   * Maneja el envío de mensajes con integración al backend
   */
  const handleSendMessage = async () => {
    const userMessage = chatData.currentMessage.trim();
    if (!userMessage || isLoading) return;

    console.log('🚀 ENVIANDO MENSAJE:', userMessage);

    // 1. Limpiar input
    setChatData(prev => ({
      ...prev,
      currentMessage: ''
    }));

    // 2. Agregar mensaje del usuario
    const userMsg = {
      type: 'user',
      content: userMessage,
      timestamp: new Date(),
      id: `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };

    setChatData(prev => ({
      ...prev,
      chatHistory: Array.isArray(prev.chatHistory) ? [...prev.chatHistory, userMsg] : [userMsg]
    }));

    // 3. Activar loading
    setIsLoading(true);

    try {
      const response = await callBackendGuide(userMessage);
      console.log('📨 RESPUESTA RECIBIDA:', response);

      if (!response) {
        throw new Error('Respuesta vacía del backend');
      }

      // 4. Agregar respuesta del backend
      const botMsg = {
        type: 'ratoncito',
        content: response,
        timestamp: new Date(),
        id: `bot_${Date.now()}`
      };

      setChatData(prev => ({
        ...prev,
        chatHistory: [...prev.chatHistory, botMsg]
      }));

      console.log('✅ MENSAJE AGREGADO CORRECTAMENTE');

    } catch (error) {
      console.error('❌ ERROR:', error);
      
      const errorMsg = {
        type: 'ratoncito',
        content: userProfile.language === 'en' 
          ? "I'm sorry, I'm having trouble connecting right now. Please try again in a moment! 🐭✨"
          : "Lo siento, tengo problemas para conectarme ahora. ¡Inténtalo de nuevo en un momento! 🐭✨",
        timestamp: new Date(),
        id: `error_${Date.now()}`
      };

      setChatData(prev => ({
        ...prev,
        chatHistory: [...prev.chatHistory, errorMsg]
      }));
    } finally {
      setIsLoading(false);
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
    
    // Función para formatear texto de Markdown básico
    const formatText = (text) => {
      if (!text) return '';
      
      return text
        .split('\n\n')
        .map((paragraph, i) => (
          <div key={i} className="mb-3 last:mb-0">
            {paragraph.split('\n').map((line, j) => (
              <div key={j}>
                {line.split('**').map((part, k) => 
                  k % 2 === 0 ? part : <strong key={k}>{part}</strong>
                )}
              </div>
            ))}
          </div>
        ));
    };
    
    return (
      <div 
        key={message.id || index} 
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div 
          className={`
            ${isUser ? 'max-w-xs lg:max-w-md' : 'max-w-md lg:max-w-lg'} px-4 py-3 rounded-lg font-body
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
          <div className="text-sm leading-relaxed">
            {formatText(message.content || '')}
          </div>
          
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
        <div className="max-w-2xl mx-auto">
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
            <div className="flex-1">
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
            <div className="flex flex-col items-end">
              <div className={`w-3 h-3 rounded-full ${USE_MOCK_BACKEND ? 'bg-yellow-500' : 'bg-green-500'}`} />
              <span className="text-xs mt-1" style={{ color: COLORS.PRIMARY_BROWN }}>
                {USE_MOCK_BACKEND ? 'Demo' : 'Live'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Área de mensajes */}
      <div className="flex-1 overflow-y-auto p-4 pb-24">
        <div className="max-w-2xl mx-auto">
          
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

          {/* Mensajes del chat */}
          {(chatData.chatHistory || []).map((message, index) => {
            return (
              <div key={`message-${message.id}-${index}`}>
                {renderMessage(message, index)}
              </div>
            );
          })}

          {/* Indicador de carga */}
          {(isTyping || isLoading) && (
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
                      ? (isLoading ? 'Thinking...' : 'Tooth Mouse is typing')
                      : (isLoading ? 'Pensando...' : 'Ratoncito Pérez está escribiendo')
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

          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Input del chat */}
      <div 
        className="fixed bottom-0 left-0 right-0 p-4 border-t"
        style={{ 
          backgroundColor: COLORS.WHITE,
          borderColor: COLORS.GRAY_LIGHT 
        }}
      >
        <div className="max-w-2xl mx-auto">
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
              disabled={isTyping || isLoading}
            />
            
            {/* Botón de micrófono */}
            {speechSupported && (
              <Button
                variant={isListening ? "secondary" : "primary"}
                onClick={toggleSpeechRecognition}
                disabled={isTyping || isLoading}
                className="px-4"
                title={userProfile.language === 'en' 
                  ? (isListening ? 'Stop listening' : 'Start voice input')
                  : (isListening ? 'Dejar de escuchar' : 'Iniciar entrada de voz')
                }
              >
                {isListening ? (
                  <MicOff 
                    className="w-5 h-5 animate-pulse" 
                    style={{ color: COLORS.SECONDARY_RED }}
                  />
                ) : (
                  <Mic className="w-5 h-5" />
                )}
              </Button>
            )}

            {/* Botón de altavoz para leer la última respuesta */}
            {speechSynthesisSupported && (
              <Button
                variant={isSpeaking ? "secondary" : "primary"}
                onClick={speakLastResponse}
                disabled={isTyping || isLoading || chatData.chatHistory.filter(msg => msg.type === 'ratoncito').length === 0}
                className="px-4"
                title={userProfile.language === 'en' 
                  ? (isSpeaking ? 'Stop reading' : 'Read last response aloud')
                  : (isSpeaking ? 'Dejar de leer' : 'Leer última respuesta en voz alta')
                }
              >
                {isSpeaking ? (
                  <VolumeX 
                    className="w-5 h-5 animate-pulse" 
                    style={{ color: COLORS.SECONDARY_RED }}
                  />
                ) : (
                  <Volume2 className="w-5 h-5" />
                )}
              </Button>
            )}
            
            <Button
              variant="secondary"
              onClick={handleSendMessage}
              disabled={!chatData.currentMessage.trim() || isTyping || isLoading}
              className="px-4"
            >
              <Send className="w-5 h-5" />
            </Button>
          </div>

          {/* Indicador de estado de voz */}
          {isListening && (
            <div 
              className="mt-2 text-center text-sm font-body animate-pulse"
              style={{ color: COLORS.SECONDARY_RED }}
            >
              {userProfile.language === 'en' 
                ? '🎤 Listening... Speak now!'
                : '🎤 Escuchando... ¡Habla ahora!'
              }
            </div>
          )}

          {/* Indicador de síntesis de voz */}
          {isSpeaking && (
            <div 
              className="mt-2 text-center text-sm font-body animate-pulse"
              style={{ color: COLORS.SECONDARY_BLUE }}
            >
              {userProfile.language === 'en' 
                ? '🔊 Reading aloud...'
                : '🔊 Leyendo en voz alta...'
              }
            </div>
          )}

          {!speechSupported && !speechSynthesisSupported && (
            <div 
              className="mt-2 text-center text-xs font-body opacity-60"
              style={{ color: COLORS.PRIMARY_BROWN }}
            >
              {userProfile.language === 'en' 
                ? '⚠️ Voice features not available in this browser'
                : '⚠️ Funciones de voz no disponibles en este navegador'
              }
            </div>
          )}

          {(speechSupported || speechSynthesisSupported) && !(speechSupported && speechSynthesisSupported) && (
            <div 
              className="mt-2 text-center text-xs font-body opacity-60"
              style={{ color: COLORS.PRIMARY_BROWN }}
            >
              {userProfile.language === 'en' 
                ? (speechSupported ? '⚠️ Voice output not available' : '⚠️ Voice input not available')
                : (speechSupported ? '⚠️ Salida de voz no disponible' : '⚠️ Entrada de voz no disponible')
              }
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
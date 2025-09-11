import { useState, useEffect, useRef } from 'react';
import { getTimeBasedGreeting } from '../utils/dateUtils';

/**
 * Hook personalizado para manejar el sistema de chat con el Ratoncito Pérez
 */
export const useChat = (userProfile) => {
  const [chatHistory, setChatHistory] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef(null);

  // Auto-scroll al final del chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);
  /**
   * Genera respuestas contextuales del Rey Niño Buby
   * @param {string} message - Mensaje del usuario
   * @returns {string} Respuesta del Rey Niño Buby
   */
  const generateReyNinoBubyResponse = (message) => {
    const isChild = userProfile.type === 'child';
    const isEnglish = userProfile.language === 'en';
      // Respuestas en inglés para niños
    const childResponsesEN = [
      "👑✨ Hello little adventurer! Would you like to play a royal treasure hunt in Madrid?",
      "How exciting! I know a super fun royal game in this place. Can you count how many windows you see?",
      "You have an incredible imagination! Did you know I keep my royal treasures here?",
      "I love talking to you! Would you like me to tell you the royal secret of this magical place?",
      "🎮 Let's play! Can you find three things that are golden like my royal crown?",
      "✨ Royal question: If you could rule like me, where in Madrid would you build your castle first?"
    ];

    // Respuestas en inglés para adultos
    const parentResponsesEN = [
      "As a parent, I can tell you this place has a rich cultural history dating back to the 16th century.",
      "It's interesting how we can combine fun and learning in these emblematic places of Madrid.",
      "From an educational perspective, this site offers multiple learning opportunities for the whole family.",
      "Madrid's history can be perfectly appreciated from this strategic point in the city.",
      "This location offers excellent family activities with educational components suitable for all ages."
    ];    // Respuestas en español para niños
    const childResponsesES = [
      "👑✨ ¡Hola pequeño aventurero! ¿Te gustaría jugar a encontrar tesoros reales por Madrid?",
      "¡Qué emocionante! Conozco un juego real súper divertido en este lugar. ¿Puedes contar cuántas ventanas ves?",
      "¡Tienes una imaginación increíble! ¿Sabías que aquí guardo mis tesoros reales más preciados?",
      "¡Me encanta hablar contigo! ¿Quieres que te cuente el secreto real de este lugar mágico?",
      "🎮 ¡Vamos a jugar! ¿Puedes encontrar tres cosas que sean doradas como mi corona real?",
      "✨ Pregunta real: Si pudieras gobernar como yo, ¿dónde construirías tu castillo primero en Madrid?"
    ];

    // Respuestas en español para adultos
    const parentResponsesES = [
      "Como padre/madre, te cuento que este lugar tiene una rica historia cultural que data del siglo XVI.",
      "Es interesante cómo podemos combinar diversión y aprendizaje en estos lugares emblemáticos de Madrid.",
      "Desde una perspectiva educativa, este sitio ofrece múltiples oportunidades de aprendizaje para toda la familia.",
      "La historia de Madrid se puede apreciar perfectamente desde este punto estratégico de la ciudad.",
      "Este lugar ofrece excelentes actividades familiares con componentes educativos apropiados para todas las edades."
    ];

    // Seleccionar el array de respuestas apropiado
    let responses;
    if (isEnglish) {
      responses = isChild ? childResponsesEN : parentResponsesEN;
    } else {
      responses = isChild ? childResponsesES : parentResponsesES;
    }

    return responses[Math.floor(Math.random() * responses.length)];
  };

  /**
   * Envía un mensaje al chat
   * @param {string} message - Mensaje a enviar (opcional, usa currentMessage si no se proporciona)
   */
  const sendMessage = async (message = currentMessage) => {
    if (!message.trim()) return;

    const userMsg = {
      type: 'user',
      content: message.trim(),
      timestamp: new Date(),
      id: Date.now()
    };

    setChatHistory(prev => [...prev, userMsg]);
    setCurrentMessage('');
    setIsTyping(true);    // Simular tiempo de respuesta del Rey Niño Buby
    setTimeout(() => {
      const response = generateReyNinoBubyResponse(message);
        setChatHistory(prev => [...prev, {
        type: 'rey',
        content: response,
        timestamp: new Date(),
        id: Date.now() + 1
      }]);
      
      setIsTyping(false);
    }, 1000 + Math.random() * 1500); // Entre 1 y 2.5 segundos
  };

  /**
   * Añade un mensaje del sistema (para navegación, etc.)
   * @param {string} content - Contenido del mensaje
   */
  const addSystemMessage = (content) => {
    setChatHistory(prev => [...prev, {
      type: 'system',
      content,
      timestamp: new Date(),
      id: Date.now()
    }]);
  };

  /**
   * Limpia todo el historial del chat
   */
  const clearChat = () => {
    setChatHistory([]);
  };

  /**
   * Añade mensaje de bienvenida inicial
   */
  const addWelcomeMessage = () => {
    // Solo agregar si no hay mensajes ya en el historial
    setChatHistory(prev => {
      if (prev.length > 0) {
        console.log('Ya hay mensajes, no agregar bienvenida duplicada');
        return prev; // No agregar si ya hay mensajes
      }
      
      const greeting = getTimeBasedGreeting();
      const isChild = userProfile.type === 'child';
      const isEnglish = userProfile.language === 'en';
        let welcomeMessage;
      if (isEnglish) {
        welcomeMessage = isChild 
          ? `${greeting} little adventurer! 👑✨ I'm King Boy Buby and I'm here to show you the royal secrets of Madrid. Ready for an incredible royal adventure?`
          : `${greeting}! I'm here to enrich your family visit to Madrid with fascinating cultural information and stories.`;
      } else {
        welcomeMessage = isChild
          ? `${greeting} pequeño aventurero! 👑✨ Soy el Rey Niño Buby y estoy aquí para mostrarte los secretos reales de Madrid. ¿Estás listo para una aventura real increíble?`
          : `${greeting}! Estoy aquí para enriquecer su visita familiar a Madrid con información cultural e historias fascinantes.`;
      }      return [{
        type: 'rey',
        content: welcomeMessage,
        timestamp: new Date(),
        id: Date.now()
      }];
    });
  };

  /**
   * Actualiza el historial de chat directamente
   * @param {Array} newHistory - Nuevo historial completo
   */
  const updateChatHistory = (newHistory) => {
    console.log('🔥 updateChatHistory llamado en useChat:', newHistory);
    setChatHistory(newHistory);
  };

  /**
   * Añade un mensaje al historial de chat
   * @param {Object} message - Mensaje a añadir
   */
  const addMessage = (message) => {
    console.log('🔥 addMessage llamado en useChat:', message);
    setChatHistory(prev => [...prev, message]);
  };

  return {
    chatHistory,
    currentMessage,
    setCurrentMessage,
    isTyping,
    sendMessage,
    addSystemMessage,
    clearChat,
    addWelcomeMessage,
    chatEndRef,
    // ✅ NUEVAS funciones para actualizar el historial
    updateChatHistory,
    addMessage
  };
};

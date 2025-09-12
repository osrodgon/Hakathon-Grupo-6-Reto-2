import React, { useState, useEffect } from 'react';
import { useUserProfile } from './hooks/useUserProfile';
import { useChat } from './hooks/useChat';
import { getCurrentLocation } from './utils/locationUtils';

// Importar páginas
import LoadingPage from './pages/LoadingPage';
import ProfilePage from './pages/ProfilePage';
import HomePage from './pages/HomePage';
import ChatPage from './pages/ChatPage';
import MapPage from './pages/MapPage';
import AboutPage from './pages/AboutPage';

// Importar componentes
import FloatingMenu from './components/navigation/FloatingMenu';

/**
 * Componente principal de la aplicación Ratoncito Pérez Madrid
 * Maneja la navegación entre pantallas y el estado global de la aplicación
 */
const App = () => {
  // Estado principal de navegación
  const [currentScreen, setCurrentScreen] = useState('loading');
  const [userLocation, setUserLocation] = useState(null);

  // Hooks personalizados
  const {
    userProfile,
    updateProfile,
    completeProfile,
    getPersonalizedGreeting
  } = useUserProfile();

  const {
    chatHistory,
    currentMessage,
    setCurrentMessage,
    isTyping,
    sendMessage,
    addSystemMessage,
    clearChat,
    addWelcomeMessage,
    chatEndRef,
    updateChatHistory,
    addMessage
  } = useChat(userProfile);

  // Obtener ubicación del usuario al iniciar la aplicación
  useEffect(() => {
    getCurrentLocation()
      .then(location => {
        setUserLocation(location);
      })
      .catch(error => {
        console.warn('Error getting user location:', error);
        // Ubicación por defecto: Puerta del Sol, Madrid
        setUserLocation({ lat: 40.4168, lng: -3.7038 });
      });
  }, []);
  // Verificar si el usuario ya tiene un perfil configurado
  useEffect(() => {
    if (currentScreen === 'loading') {
      // La pantalla de loading se encargará de la transición
      return;
    }
    
    // No redirigir automáticamente del profile - permitir acceso siempre
  }, [userProfile, currentScreen]);

  /**
   * Maneja la navegación entre pantallas
   * @param {string} screen - Nombre de la pantalla a mostrar
   */
  const handleNavigation = (screen) => {
    setCurrentScreen(screen);
    
    // Añadir mensaje de bienvenida cuando se va al chat por primera vez
    if (screen === 'chat' && chatHistory.length === 0) {
      setTimeout(() => {
        addWelcomeMessage();
      }, 500);
    }
  };

  /**
   * Completa la pantalla de carga
   */
  const handleLoadingComplete = () => {
    if (userProfile.isFirstTime) {
      setCurrentScreen('profile');
    } else {
      setCurrentScreen('home');
    }
  };

  /**
   * Completa la configuración del perfil
   */
  const handleProfileComplete = () => {
    completeProfile();
    setCurrentScreen('home');
  };

  /**
   * Datos del chat para pasar a la página de chat
   */
  const chatData = {
    chatHistory,
    currentMessage
  };

  /**
   * Función para actualizar datos del chat
   */
  const setChatData = (updater) => {
    console.log('🔥 setChatData llamado en App.jsx');
    console.log('🔥 chatData actual:', chatData);
    
    if (typeof updater === 'function') {
      const newData = updater(chatData);
      console.log('🔥 newData calculado:', newData);
      
      // Actualizar currentMessage si cambió
      if (newData.currentMessage !== undefined && newData.currentMessage !== chatData.currentMessage) {
        console.log('🔥 Actualizando currentMessage:', newData.currentMessage);
        setCurrentMessage(newData.currentMessage);
      }
      
      // ✅ ARREGLO: Actualizar chatHistory si cambió
      if (newData.chatHistory !== undefined && newData.chatHistory !== chatData.chatHistory) {
        console.log('🔥 Actualizando chatHistory, nueva longitud:', newData.chatHistory.length);
        console.log('🔥 Usando updateChatHistory del hook useChat');
        updateChatHistory(newData.chatHistory);
      }
    }
  };

  /**
   * Renderiza la pantalla actual
   */
  const renderCurrentScreen = () => {
    switch (currentScreen) {
      case 'loading':
        return (
          <LoadingPage 
            onComplete={handleLoadingComplete}
          />
        );

      case 'profile':
        return (
          <ProfilePage
            userProfile={userProfile}
            updateProfile={updateProfile}
            onComplete={handleProfileComplete}
          />
        );

      case 'home':
        return (
          <HomePage
            userProfile={userProfile}
            onNavigate={handleNavigation}
            getPersonalizedGreeting={getPersonalizedGreeting}
          />
        );

      case 'chat':
        return (
          <ChatPage
            userProfile={userProfile}
            chatData={chatData}
            setChatData={setChatData}
            chatEndRef={chatEndRef}
            isTyping={isTyping}
          />
        );

      case 'map':
        return (
          <MapPage
            userProfile={userProfile}
            onNavigate={handleNavigation}
            addSystemMessage={addSystemMessage}
            userLocation={userLocation}
          />
        );

      case 'about':
        return (
          <AboutPage
            userProfile={userProfile}
            onNavigate={handleNavigation}
          />
        );

      default:
        return (
          <div className="min-h-screen flex items-center justify-center">
            <p>Pantalla no encontrada</p>
          </div>
        );
    }
  };

  /**
   * Determina si mostrar el menú flotante
   */
  const shouldShowFloatingMenu = () => {
    return currentScreen !== 'loading' && currentScreen !== 'profile';
  };

  return (
    <div className="min-h-screen">
      {/* Renderizar pantalla actual */}
      {renderCurrentScreen()}

      {/* Menú flotante de navegación */}
      {shouldShowFloatingMenu() && (
        <FloatingMenu 
          onNavigate={handleNavigation}
          currentScreen={currentScreen}
        />
      )}
    </div>
  );
};

export default App;

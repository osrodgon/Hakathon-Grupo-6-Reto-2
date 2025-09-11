import { useState, useEffect } from 'react';

/**
 * Hook personalizado para manejar el perfil de usuario
 * Incluye persistencia en localStorage
 */
export const useUserProfile = () => {
  const [userProfile, setUserProfile] = useState(() => {
    // Intentar cargar perfil guardado del localStorage
    const savedProfile = localStorage.getItem('ratoncitoPerez_userProfile');
    if (savedProfile) {
      try {
        return JSON.parse(savedProfile);
      } catch (error) {
        console.warn('Error loading saved profile:', error);
      }
    }
    
    // Perfil por defecto
    return {
      type: 'child', // child, parent
      language: 'es', // es, en
      accessibility: 'none', // none, visual, hearing, mobility
      name: '',
      age: null,
      favoriteColor: 'yellow',
      isFirstTime: true
    };
  });

  // Guardar perfil en localStorage cuando cambie
  useEffect(() => {
    localStorage.setItem('ratoncitoPerez_userProfile', JSON.stringify(userProfile));
  }, [userProfile]);

  /**
   * Actualiza el perfil de usuario
   * @param {Object} updates - Campos a actualizar
   */
  const updateProfile = (updates) => {
    setUserProfile(prev => ({
      ...prev,
      ...updates
    }));
  };

  /**
   * Marca el perfil como completado (no es primera vez)
   */
  const completeProfile = () => {
    updateProfile({ isFirstTime: false });
  };

  /**
   * Resetea el perfil a valores por defecto
   */
  const resetProfile = () => {
    localStorage.removeItem('ratoncitoPerez_userProfile');
    setUserProfile({
      type: 'child',
      language: 'es', 
      accessibility: 'none',
      name: '',
      age: null,
      favoriteColor: 'yellow',
      isFirstTime: true
    });
  };

  /**
   * Obtiene el saludo personalizado basado en el perfil
   */
  const getPersonalizedGreeting = () => {
    const { type, name, language } = userProfile;
    
    if (language === 'en') {
      if (name) {
        return type === 'child' ? `Hello ${name}!` : `Hello, ${name}'s family!`;
      }
      return type === 'child' ? 'Hello little adventurer!' : 'Hello family!';
    }
    
    // Español por defecto
    if (name) {
      return type === 'child' ? `¡Hola ${name}!` : `¡Hola familia de ${name}!`;
    }
    return type === 'child' ? '¡Hola pequeño aventurero!' : '¡Hola familia!';
  };

  return {
    userProfile,
    updateProfile,
    completeProfile,
    resetProfile,
    getPersonalizedGreeting
  };
};

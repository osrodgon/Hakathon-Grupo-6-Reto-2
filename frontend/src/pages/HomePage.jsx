import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, Map, Gift, Sparkles, Calendar, MapPin, Cloud, Camera, X } from 'lucide-react';
import Button from '../components/common/Button';
import Card, { CardTitle, CardContent } from '../components/common/Card';
import { COLORS, API_CONFIG } from '../config/constants';
import { getTimeBasedGreeting } from '../utils/dateUtils';
import { getCurrentLocation } from '../utils/locationUtils';

/**
 * Página principal de la aplicación
 * Muestra opciones principales y actividades sugeridas
 * @param {Object} props
 * @param {Object} props.userProfile - Perfil del usuario
 * @param {function} props.onNavigate - Función de navegación
 * @param {function} props.getPersonalizedGreeting - Función para obtener saludo personalizado
 */
const HomePage = ({ userProfile, onNavigate, getPersonalizedGreeting }) => {
  
  // Estado para el pronóstico del tiempo
  const [forecast, setForecast] = useState(null);
  const [isLoadingWeather, setIsLoadingWeather] = useState(false);

  // Estados para la cámara
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [stream, setStream] = useState(null);
  const [error, setError] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isRealtimeMode, setIsRealtimeMode] = useState(false);
  const [wsConnection, setWsConnection] = useState(null);
  const [lastAnalysisTime, setLastAnalysisTime] = useState(0);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);
  const realtimeAnalysisRef = useRef(null);
  const keepAliveRef = useRef(null);

  /**
   * Obtiene el pronóstico del tiempo desde el backend
   */
  const getForecast = async () => {
    try {
      setIsLoadingWeather(true);
      
      // Obtener ubicación del usuario
      const location = await getCurrentLocation();
      
      // Llamar al endpoint /forecast
      const response = await fetch(
        `${API_CONFIG.BASE_URL}/forecast?lat=${location.lat}&lon=${location.lng}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setForecast(data);
      } else {
        console.error('Error obteniendo pronóstico:', response.statusText);
      }
    } catch (error) {
      console.error('Error en la llamada al pronóstico:', error);
    } finally {
      setIsLoadingWeather(false);
    }
  };

  // Obtener pronóstico al cargar el componente
  useEffect(() => {
    getForecast();
  }, []);

  /**
   * Abre la cámara del dispositivo
   */
  const openCamera = async () => {
    try {
      console.log('📸 ABRIENDO CÁMARA - Iniciando...');
      setError(null);
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment' // Usar cámara trasera por defecto
        } 
      });
      console.log('📸 CÁMARA ABIERTA - Stream obtenido');
      setStream(mediaStream);
      setIsCameraOpen(true);
      
      // Asignar el stream al elemento video cuando esté disponible
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        console.log('📸 VIDEO CONFIGURADO - Stream asignado al video');
      }

      // Iniciar automáticamente el análisis en tiempo real
      setTimeout(() => {
        console.log('🔌 AUTO-CONECTANDO WebSocket después de abrir cámara...');
        connectToVisionWebSocket();
      }, 1000); // Esperar 1 segundo para que el video se inicialice
      
    } catch (err) {
      console.error('Error accessing camera:', err);
      setError(userProfile.language === 'en' 
        ? 'Cannot access camera. Please check permissions.' 
        : 'No se puede acceder a la cámara. Verifica los permisos.'
      );
    }
  };

  /**
   * Cierra la cámara y libera los recursos
   */
  const closeCamera = () => {
    console.log('📸 CERRANDO CÁMARA - Iniciando proceso...');
    console.log('🔍 STACK TRACE - Llamado desde:');
    console.trace();
    
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      console.log('📸 STREAM CERRADO - Tracks detenidos');
    }
    
    // Cerrar WebSocket si está conectado
    if (wsConnection) {
      console.log('🔌 CERRANDO WebSocket - Desconectando...');
      wsConnection.close(1000, 'Camera closed'); // Código de cierre normal
      setWsConnection(null);
      setIsRealtimeMode(false);
      setIsAnalyzing(false);
      console.log('🔌 WebSocket CERRADO');
    }
    
    // Limpiar intervalos
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
      console.log('⏱️ INTERVALO PRINCIPAL limpiado');
    }
    
    if (realtimeAnalysisRef.current) {
      clearInterval(realtimeAnalysisRef.current);
      realtimeAnalysisRef.current = null;
      console.log('⏱️ INTERVALO ANÁLISIS limpiado');
    }
    
    if (keepAliveRef.current) {
      clearInterval(keepAliveRef.current);
      keepAliveRef.current = null;
      console.log('⏱️ KEEP-ALIVE limpiado');
    }
    
    setIsCameraOpen(false);
    setError(null);
    setIsAnalyzing(false);
    setAnalysisResult(null);
    setIsRealtimeMode(false);
    setLastAnalysisTime(0);
    console.log('📸 CÁMARA COMPLETAMENTE CERRADA');
  };

  /**
   * Conectar al WebSocket para análisis en tiempo real
   */
  const connectToVisionWebSocket = () => {
    try {
      const wsUrl = `ws://localhost:8000/ws/vision-stream`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('🔌 Conectado al WebSocket de visión');
        setWsConnection(ws);
        setIsRealtimeMode(true);
        startRealtimeAnalysis(ws);
        startKeepAlive(ws);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      ws.onclose = (event) => {
        console.log('🔌 WebSocket desconectado', event.code, event.reason);
        setWsConnection(null);
        setIsRealtimeMode(false);
        setIsAnalyzing(false);
        
        // Solo intentar reconectar si:
        // 1. La cámara sigue abierta
        // 2. No fue un cierre normal (código 1000)
        // 3. No fue porque se cerró la cámara intencionalmente
        if (isCameraOpen && event.code !== 1000 && event.reason !== 'Camera closed' && event.reason !== 'Component unmounting') {
          console.log('🔄 Reconexión necesaria, intentando en 3 segundos...');
          setTimeout(() => {
            if (isCameraOpen) { // Verificar nuevamente antes de reconectar
              console.log('🔄 Intentando reconectar WebSocket...');
              connectToVisionWebSocket();
            }
          }, 3000);
        } else {
          console.log('🔌 Cierre normal del WebSocket, no se reintentará conexión');
        }
      };
      
      ws.onerror = (error) => {
        console.error('❌ Error en WebSocket:', error);
        setError(userProfile.language === 'en' 
          ? 'Error connecting to real-time analysis. Reconnecting...' 
          : 'Error conectando al análisis en tiempo real. Reconectando...'
        );
      };
      
    } catch (err) {
      console.error('Error creando WebSocket:', err);
      setError(userProfile.language === 'en' 
        ? 'Cannot start real-time analysis.' 
        : 'No se puede iniciar el análisis en tiempo real.'
      );
    }
  };

  /**
   * Iniciar keep-alive para mantener la conexión WebSocket activa
   */
  const startKeepAlive = (ws) => {
    if (keepAliveRef.current) {
      clearInterval(keepAliveRef.current);
    }
    
    keepAliveRef.current = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Ping cada 30 segundos
  };

  /**
   * Manejar mensajes del WebSocket
   */
  const handleWebSocketMessage = (data) => {
    const timestamp = new Date().toLocaleTimeString();
    
    switch (data.type) {
      case 'status':
        console.log(`📡 [${timestamp}] Estado:`, data.data.message);
        break;
        
      case 'analysis':
        const frameNum = data.data.frame_number;
        const sessionTime = data.data.session_duration;
        const fps = data.data.fps_average;
        
        console.log(`� [${timestamp}] FRAME #${frameNum} PROCESADO`);
        console.log(`   � Sesión: ${sessionTime} | FPS: ${fps}`);
        
        setAnalysisResult({
          message: data.data.message,
          description: data.data.description,
          location: `Frame #${frameNum}`,
          confidence: data.data.confidence,
          processing_time: data.data.processing_time,
          frame_number: frameNum,
          session_duration: sessionTime,
          fps_average: fps,
          timestamp: timestamp
        });
        setIsAnalyzing(false);
        setLastAnalysisTime(Date.now());
        
        // Log milestone cada 10 frames
        if (frameNum % 10 === 0) {
          console.log(`🎯 MILESTONE FRONTEND: ${frameNum} frames - ${sessionTime} - ${fps} FPS`);
        }
        
        break;
        
      case 'error':
        console.error('❌ Error de análisis:', data.data.message);
        setError(data.data.message);
        setIsAnalyzing(false);
        break;
        
      case 'pong':
        // Respuesta al ping - conexión activa
        console.log('💓 WebSocket activo');
        break;
        
      default:
        console.log('📡 Mensaje desconocido:', data);
    }
  };

  /**
   * Iniciar análisis en tiempo real
   */
  const startRealtimeAnalysis = (ws) => {
    console.log('🚀 INICIANDO ANÁLISIS EN TIEMPO REAL - Modo enumeración simple');
    
    if (realtimeAnalysisRef.current) {
      clearInterval(realtimeAnalysisRef.current);
      console.log('⏱️ Limpiando intervalo anterior...');
    }
    
    // Función que ejecuta la captura y envío
    const executeFrameCapture = () => {
      const timestamp = new Date().toLocaleTimeString();
      console.log(`� [${timestamp}] Capturando y enviando frame...`);
      
      if (ws && ws.readyState === WebSocket.OPEN && videoRef.current) {
        const frameData = captureFrame();
        if (frameData) {
          setIsAnalyzing(true);
          
          const message = JSON.stringify({
            type: 'frame',
            data: frameData.split(',')[1] // Remover el prefijo data:image/jpeg;base64,
          });
          
          try {
            ws.send(message);
            console.log(`✅ [${timestamp}] Frame enviado exitosamente`);
          } catch (error) {
            console.error(`❌ [${timestamp}] Error enviando frame:`, error);
          }
        } else {
          console.log(`❌ [${timestamp}] No se pudo capturar frame`);
        }
      } else {
        console.log(`🔌 [${timestamp}] WebSocket no disponible (estado: ${ws ? ws.readyState : 'null'})`);
      }
    };
    
    // Ejecutar inmediatamente una vez
    console.log('🧪 EJECUTANDO PRIMERA CAPTURA INMEDIATAMENTE...');
    setTimeout(() => {
      executeFrameCapture();
    }, 500);
    
    // Configurar intervalo
    console.log('⏱️ Configurando nuevo intervalo cada 3 segundos...');
    let intervalCount = 0;
    
    realtimeAnalysisRef.current = setInterval(() => {
      intervalCount++;
      const intervalTimestamp = new Date().toLocaleTimeString();
      console.log(`⏰ [${intervalTimestamp}] INTERVALO #${intervalCount} EJECUTÁNDOSE - Intentando enviar frame...`);
      console.log(`   🔍 WebSocket estado: ${ws ? ws.readyState : 'null'} (1=OPEN)`);
      console.log(`   📹 Video disponible: ${!!videoRef.current}`);
      console.log(`   🔗 WS referencia válida: ${!!ws}`);
      
      if (!ws) {
        console.log('❌ WebSocket es null! Deteniendo intervalo...');
        clearInterval(realtimeAnalysisRef.current);
        return;
      }
      
      if (ws.readyState !== WebSocket.OPEN) {
        console.log(`❌ WebSocket no está abierto (estado: ${ws.readyState})! Deteniendo intervalo...`);
        clearInterval(realtimeAnalysisRef.current);
        return;
      }
      
      executeFrameCapture();
    }, 3000); // 3 segundos para facilitar seguimiento
    
    console.log('✅ ANÁLISIS TIEMPO REAL CONFIGURADO - ID del intervalo:', realtimeAnalysisRef.current);
    
    // Verificar que el intervalo está funcionando
    setTimeout(() => {
      console.log('🔍 VERIFICACIÓN - El intervalo sigue activo:', !!realtimeAnalysisRef.current);
    }, 3000);
  };

  /**
   * Captura un frame del video
   */
  const captureFrame = () => {
    console.log('📸 CAPTURE_FRAME - Iniciando captura...');
    
    if (!videoRef.current || !canvasRef.current) {
      console.log('❌ CAPTURE_FRAME - Referencias no disponibles');
      console.log('  videoRef.current:', !!videoRef.current);
      console.log('  canvasRef.current:', !!canvasRef.current);
      return null;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    console.log(`📏 VIDEO DIMENSIONS - ${video.videoWidth}x${video.videoHeight}`);

    // Configurar el tamaño del canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Dibujar el frame actual
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    console.log(`🎨 CANVAS - Frame dibujado en canvas ${canvas.width}x${canvas.height}`);

    // Convertir a base64
    const dataURL = canvas.toDataURL('image/jpeg', 0.7);
    console.log(`🔢 BASE64 - Tamaño: ${dataURL.length} caracteres`);
    console.log(`✅ CAPTURE_FRAME - Completado exitosamente`);
    
    return dataURL;
  };

  /**
   * Efecto para asignar el stream al video cuando esté disponible
   */
  useEffect(() => {
    if (videoRef.current && stream) {
      console.log('📺 ASIGNANDO STREAM - Configurando srcObject...');
      videoRef.current.srcObject = stream;
      
      // Añadir listener para cuando los metadatos del video estén cargados
      const video = videoRef.current;
      const onLoadedMetadata = () => {
        console.log(`📺 VIDEO LISTO - Dimensiones: ${video.videoWidth}x${video.videoHeight}`);
        console.log('📺 VIDEO METADATA CARGADA - Video completamente inicializado');
      };
      
      video.addEventListener('loadedmetadata', onLoadedMetadata);
      
      // Cleanup function
      return () => {
        if (video) {
          video.removeEventListener('loadedmetadata', onLoadedMetadata);
        }
      };
    }
  }, [stream]);

  /**
   * Limpiar recursos al desmontar el componente
   * COMENTADO TEMPORALMENTE - Para evitar que se cierre la cámara automáticamente
   */
  useEffect(() => {
    return () => {
      // COMENTADO: No cerrar automáticamente el stream
      // if (stream) {
      //   stream.getTracks().forEach(track => track.stop());
      // }
      console.log('🔄 useEffect cleanup - Stream mantenido activo para evaluación');
    };
  }, [stream]);

  /**
   * Limpiar conexión WebSocket al desmontar el componente
   */
  useEffect(() => {
    return () => {
      if (wsConnection) {
        console.log('🧹 Limpiando conexión WebSocket al desmontar componente');
        wsConnection.close(1000, 'Component unmounting'); // Código de cierre normal
        setWsConnection(null);
      }
      // Limpiar timers si existen
      if (realtimeAnalysisRef.current) {
        clearInterval(realtimeAnalysisRef.current);
      }
      if (keepAliveRef.current) {
        clearInterval(keepAliveRef.current);
      }
    };
  }, [wsConnection]);
  
  /**
   * Obtiene el juego o actividad del día según el tipo de usuario
   */
  const getDailyActivity = () => {
    const isChild = userProfile.type === 'child';
    const isEnglish = userProfile.language === 'en';
    
    const childActivities = {
      es: [
        "🔍 Encuentra 3 lugares en Madrid donde pueda esconder mis moneditas mágicas",
        "🎭 Descubre qué estatua guarda el secreto del tesoro perdido",
        "🌟 Busca las 5 ventanas más bonitas del Palacio Real",
        "🐭 Ayúdame a encontrar el mejor escondite para mis aventuras"
      ],
      en: [
        "🔍 Find 3 places in Madrid where I can hide my magical coins",
        "🎭 Discover which statue guards the secret of the lost treasure",
        "🌟 Look for the 5 most beautiful windows of the Royal Palace",
        "🐭 Help me find the best hiding place for my adventures"
      ]
    };

    const parentActivities = {
      es: [
        "📚 Ruta educativa: Descubra la historia del Madrid de los Austrias",
        "🏛️ Visita cultural: Los museos más familiares de la ciudad",
        "🚶‍♂️ Paseo temático: Arquitectura y leyendas madrileñas",
        "🎨 Experiencia artística: Arte y cultura para toda la familia"
      ],
      en: [
        "📚 Educational route: Discover the history of Habsburg Madrid",
        "🏛️ Cultural visit: The most family-friendly museums in the city",
        "🚶‍♂️ Themed walk: Architecture and Madrid legends",
        "🎨 Artistic experience: Art and culture for the whole family"
      ]
    };

    const activities = isChild ? childActivities : parentActivities;
    const languageActivities = activities[isEnglish ? 'en' : 'es'];
    
    return languageActivities[Math.floor(Math.random() * languageActivities.length)];
  };

  /**
   * Obtiene recomendaciones basadas en la hora del día y el clima
   */
  const getTimeBasedRecommendation = () => {
    const hour = new Date().getHours();
    const isChild = userProfile.type === 'child';
    const isEnglish = userProfile.language === 'en';

    // Crear recomendación base según la hora
    let baseRecommendation = '';
    if (hour < 12) {
      baseRecommendation = isEnglish
        ? (isChild ? "Perfect morning for a treasure hunt in Retiro Park!" : "Great time to visit museums before they get crowded")
        : (isChild ? "¡Mañana perfecta para buscar tesoros en el Retiro!" : "Buen momento para visitar museos antes de las multitudes");
    } else if (hour < 18) {
      baseRecommendation = isEnglish
        ? (isChild ? "Afternoon adventure at Plaza Mayor awaits!" : "Ideal time for a family walk through historic Madrid")
        : (isChild ? "¡Aventura de tarde en la Plaza Mayor te espera!" : "Momento ideal para un paseo familiar por el Madrid histórico");
    } else {
      baseRecommendation = isEnglish
        ? (isChild ? "Evening magic at Templo de Debod!" : "Beautiful sunset views from Madrid's rooftops")
        : (isChild ? "¡Magia nocturna en el Templo de Debod!" : "Hermosas vistas del atardecer desde las azoteas de Madrid");
    }

    // Añadir información del clima si está disponible
    if (forecast) {
      const weatherInfo = isEnglish 
        ? ` The weather today is ${forecast.forecast} with temperatures between ${Math.round(forecast.min)}°C and ${Math.round(forecast.max)}°C.`
        : ` El clima hoy es ${forecast.forecast} con temperaturas entre ${Math.round(forecast.min)}°C y ${Math.round(forecast.max)}°C.`;
      
      return baseRecommendation + weatherInfo;
    }

    return baseRecommendation;
  };

  return (
    <div 
      className="min-h-screen p-6"
      style={{ backgroundColor: COLORS.BACKGROUND }}
    >
      <div className="max-w-md mx-auto space-y-6">
        
        {/* Encabezado de bienvenida */}
        <div className="text-center">
          <div className="relative inline-block mb-4">
            <div 
              className="w-20 h-20 rounded-full flex items-center justify-center animate-bounce-soft"
              style={{ backgroundColor: COLORS.PRIMARY_YELLOW }}
            >
              <Gift 
                className="w-10 h-10"
                style={{ color: COLORS.SECONDARY_RED }} 
              />
            </div>
            <Sparkles 
              className="absolute -top-2 -right-2 w-6 h-6 animate-pulse-glow"
              style={{ color: COLORS.SECONDARY_BLUE }} 
            />
          </div>
          
          <h1 
            className="text-3xl font-bold font-title mb-2"
            style={{ color: COLORS.PRIMARY_BROWN }}
          >
            {getPersonalizedGreeting()}
          </h1>
          
          <p 
            className="font-body text-lg"
            style={{ color: COLORS.BLACK }}
          >
            {userProfile.language === 'en'
              ? "I'm the Tooth Mouse and I'm here to show you the magical secrets of Madrid"
              : "Soy el Ratoncito Pérez y estoy aquí para mostrarte los secretos mágicos de Madrid"
            }
          </p>
        </div>

        {/* Opciones principales de navegación */}
        <Card>
          <CardTitle>
            {userProfile.language === 'en' 
              ? 'What do you want to discover today?' 
              : '¿Qué quieres descubrir hoy?'
            }
          </CardTitle>
          
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              
              {/* Botón Chat */}
              <Button
                variant="primary"
                onClick={() => onNavigate('chat')}
                className="h-20 flex-col gap-2"
              >
                <MessageCircle 
                  className="w-8 h-8"
                  style={{ color: COLORS.SECONDARY_RED }} 
                />
                <span className="text-sm font-semibold">
                  {userProfile.language === 'en' ? 'Chat' : 'Chatear'}
                </span>
              </Button>

              {/* Botón Mapa */}
              <Button
                variant="primary"
                onClick={() => onNavigate('map')}
                className="h-20 flex-col gap-2"
              >
                <Map 
                  className="w-8 h-8"
                  style={{ color: COLORS.SECONDARY_RED }} 
                />
                <span className="text-sm font-semibold">
                  {userProfile.language === 'en' ? 'Map' : 'Mapa'}
                </span>
              </Button>

              {/* Botón Cámara */}
              <Button
                variant="primary"
                onClick={() => onNavigate('camera')}
                className="h-20 flex-col gap-2 col-span-2"
              >
                <Camera 
                  className="w-8 h-8"
                  style={{ color: COLORS.SECONDARY_RED }} 
                />
                <span className="text-sm font-semibold">
                  {userProfile.language === 'en' ? 'Real-time Vision' : 'Visión en Tiempo Real'}
                </span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Modal de la cámara */}
        {isCameraOpen && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ backgroundColor: 'rgba(0, 0, 0, 0.8)' }}
          >
            <div 
              className="relative w-full max-w-md rounded-lg overflow-hidden"
              style={{ backgroundColor: COLORS.WHITE }}
            >
              {/* Encabezado del modal */}
              <div 
                className="flex justify-between items-center p-4"
                style={{ backgroundColor: COLORS.PRIMARY_YELLOW }}
              >
                <h3 
                  className="font-bold font-title"
                  style={{ color: COLORS.PRIMARY_BROWN }}
                >
                  {userProfile.language === 'en' ? '📸 Camera View' : '📸 Vista de Cámara'}
                </h3>
                <button
                  onClick={closeCamera}
                  className="p-1 rounded-full hover:bg-black hover:bg-opacity-10"
                >
                  <X 
                    className="w-6 h-6"
                    style={{ color: COLORS.PRIMARY_BROWN }}
                  />
                </button>
              </div>

              {/* Contenido del modal */}
              <div className="p-4">
                {error ? (
                  <div 
                    className="text-center p-6 rounded-lg"
                    style={{ backgroundColor: COLORS.GRAY_LIGHT }}
                  >
                    <Camera 
                      className="w-12 h-12 mx-auto mb-3"
                      style={{ color: COLORS.SECONDARY_RED }}
                    />
                    <p 
                      className="text-sm font-body"
                      style={{ color: COLORS.BLACK }}
                    >
                      {error}
                    </p>
                  </div>
                ) : analysisResult ? (
                  // Mostrar resultado del análisis
                  <div 
                    className="p-4 rounded-lg"
                    style={{ backgroundColor: COLORS.PRIMARY_YELLOW }}
                  >
                    <h4 
                      className="font-bold font-title mb-3"
                      style={{ color: COLORS.PRIMARY_BROWN }}
                    >
                      {userProfile.language === 'en' ? '🔍 Analysis Result' : '🔍 Resultado del Análisis'}
                    </h4>
                    <div 
                      className="text-sm font-body mb-3"
                      style={{ color: COLORS.BLACK }}
                    >
                      {analysisResult.message || analysisResult.description || 
                        (userProfile.language === 'en' ? 'Analysis completed!' : '¡Análisis completado!')
                      }
                    </div>
                    {analysisResult.location && (
                      <div 
                        className="text-xs font-body mb-2"
                        style={{ color: COLORS.PRIMARY_BROWN }}
                      >
                        📍 {analysisResult.location}
                      </div>
                    )}
                    {analysisResult.confidence && (
                      <div 
                        className="text-xs font-body mb-2"
                        style={{ color: COLORS.SECONDARY_BLUE }}
                      >
                        🎯 {userProfile.language === 'en' ? 'Confidence' : 'Confianza'}: {(analysisResult.confidence * 100).toFixed(1)}%
                      </div>
                    )}
                    {analysisResult.timestamp && (
                      <div 
                        className="text-xs font-body mb-2"
                        style={{ color: COLORS.SECONDARY_BLUE }}
                      >
                        🕒 {userProfile.language === 'en' ? 'Last update' : 'Última actualización'}: {analysisResult.timestamp}
                      </div>
                    )}
                    {isRealtimeMode && (
                      <div 
                        className="text-xs font-body flex items-center gap-1 animate-pulse"
                        style={{ color: COLORS.SECONDARY_RED }}
                      >
                        🔴 {userProfile.language === 'en' ? 'PERMANENT SCANNING ACTIVE' : 'ESCANEO PERMANENTE ACTIVO'}
                      </div>
                    )}
                    {isRealtimeMode && analysisResult && (
                      <div 
                        className="text-xs font-body mt-2 p-2 rounded"
                        style={{ backgroundColor: '#f0f8ff', color: COLORS.PRIMARY_BLUE }}
                      >
                        <div className="flex gap-4">
                          <span>📊 Frame #{analysisResult.frame_number || 0}</span>
                          <span>⏱️ {analysisResult.session_duration || '0s'}</span>
                          <span>📈 {analysisResult.fps_average || '0.00'} FPS</span>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="relative">
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      className="w-full h-64 object-cover rounded-lg bg-black"
                    />
                    {/* Canvas oculto para capturar fotos */}
                    <canvas
                      ref={canvasRef}
                      style={{ display: 'none' }}
                    />
                    <div 
                      className="absolute bottom-4 left-4 right-4 text-center p-2 rounded-lg"
                      style={{ backgroundColor: 'rgba(0, 0, 0, 0.7)' }}
                    >
                      <p 
                        className="text-sm font-body"
                        style={{ color: COLORS.WHITE }}
                      >
                        {userProfile.language === 'en' 
                          ? '¡Point the camera to discover Madrid with Ratón Pérez!' 
                          : '¡Apunta la cámara para descubrir Madrid con el Ratón Pérez!'
                        }
                      </p>
                      {isRealtimeMode && (
                        <p 
                          className="text-xs font-body mt-1 animate-pulse"
                          style={{ color: COLORS.PRIMARY_YELLOW }}
                        >
                          🔴 {userProfile.language === 'en' ? 'SCANNING PERMANENTLY...' : 'ESCANEANDO PERMANENTEMENTE...'}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Botones de acción */}
                <div className="mt-4 flex gap-2">
                  <Button
                    variant="secondary"
                    onClick={closeCamera}
                    className="flex-1"
                  >
                    {userProfile.language === 'en' ? 'Close' : 'Cerrar'}
                  </Button>
                  
                  {!error && !analysisResult && !isRealtimeMode && (
                    <>
                      <Button
                        variant="primary"
                        onClick={connectToVisionWebSocket}
                        className="flex-1"
                      >
                        {userProfile.language === 'en' ? 'Real-time Mode' : 'Modo Tiempo Real'}
                      </Button>
                    </>
                  )}
                  
                  {isRealtimeMode && (
                    <Button
                      variant="secondary"
                      onClick={() => {
                        if (wsConnection) {
                          wsConnection.close();
                        }
                        if (intervalRef.current) {
                          clearInterval(intervalRef.current);
                        }
                        setIsRealtimeMode(false);
                        setWsConnection(null);
                        setAnalysisResult(null);
                      }}
                      className="flex-1"
                    >
                      {userProfile.language === 'en' ? 'Stop Real-time' : 'Parar Tiempo Real'}
                    </Button>
                  )}
                  
                  {analysisResult && !isRealtimeMode && (
                    <Button
                      variant="primary"
                      onClick={() => {
                        setAnalysisResult(null);
                        setError(null);
                      }}
                      className="flex-1"
                    >
                      {userProfile.language === 'en' ? 'Analyze Again' : 'Analizar Otra Vez'}
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Información del clima */}
        {forecast && (
          <Card>
            <CardContent>
              <div 
                className="p-4 rounded-lg"
                style={{ backgroundColor: COLORS.PRIMARY_YELLOW }}
              >
                <div className="flex items-start gap-3">
                  <Cloud 
                    className="w-6 h-6 flex-shrink-0 mt-1"
                    style={{ color: COLORS.PRIMARY_BROWN }} 
                  />
                  <div>
                    <h3 
                      className="font-bold font-title mb-2"
                      style={{ color: COLORS.PRIMARY_BROWN }}
                    >
                      {userProfile.language === 'en' 
                        ? '🌤️ Today\'s Weather' 
                        : '🌤️ Clima de Hoy'
                      }
                    </h3>
                    <p 
                      className="text-sm font-body"
                      style={{ color: COLORS.BLACK }}
                    >
                      {forecast.forecast} • {Math.round(forecast.min)}°C - {Math.round(forecast.max)}°C
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Loading del clima */}
        {isLoadingWeather && !forecast && (
          <Card>
            <CardContent>
              <div 
                className="p-4 rounded-lg text-center"
                style={{ backgroundColor: COLORS.GRAY_LIGHT }}
              >
                <p 
                  className="text-sm font-body"
                  style={{ color: COLORS.BLACK }}
                >
                  {userProfile.language === 'en' 
                    ? '🌤️ Loading weather...' 
                    : '🌤️ Cargando clima...'
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Actividad del día */}
        <Card hoverable>
          <CardContent>
            <div 
              className="p-4 rounded-lg"
              style={{ backgroundColor: COLORS.SECONDARY_BLUE }}
            >
              <div className="flex items-start gap-3">
                <Calendar 
                  className="w-6 h-6 flex-shrink-0 mt-1"
                  style={{ color: COLORS.WHITE }} 
                />
                <div>
                  <h3 
                    className="font-bold font-title mb-2"
                    style={{ color: COLORS.WHITE }}
                  >
                    {userProfile.language === 'en' 
                      ? '🎮 Activity of the Day' 
                      : '🎮 Actividad del Día'
                    }
                  </h3>
                  <p 
                    className="text-sm font-body"
                    style={{ color: COLORS.WHITE }}
                  >
                    {getDailyActivity()}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recomendación basada en la hora */}
        <Card>
          <CardContent>
            <div 
              className="p-4 rounded-lg"
              style={{ backgroundColor: COLORS.PRIMARY_YELLOW }}
            >
              <div className="flex items-start gap-3">
                <MapPin 
                  className="w-6 h-6 flex-shrink-0 mt-1"
                  style={{ color: COLORS.PRIMARY_BROWN }} 
                />
                <div>
                  <h3 
                    className="font-bold font-title mb-2"
                    style={{ color: COLORS.PRIMARY_BROWN }}
                  >
                    {userProfile.language === 'en' 
                      ? '💡 Tip of the moment' 
                      : '💡 Consejo del momento'
                    }
                  </h3>
                  <p 
                    className="text-sm font-body"
                    style={{ color: COLORS.BLACK }}
                  >
                    {getTimeBasedRecommendation()}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Estadísticas de aventura para niños */}
        {userProfile.type === 'child' && (
          <Card>
            <CardTitle size="md">
              {userProfile.language === 'en' ? '🏆 Your Adventures' : '🏆 Tus Aventuras'}
            </CardTitle>
            
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div 
                    className="text-2xl font-bold font-title"
                    style={{ color: COLORS.SECONDARY_RED }}
                  >
                    3
                  </div>
                  <div 
                    className="text-xs font-body"
                    style={{ color: COLORS.BLACK }}
                  >
                    {userProfile.language === 'en' ? 'Places' : 'Lugares'}
                  </div>
                </div>
                <div>
                  <div 
                    className="text-2xl font-bold font-title"
                    style={{ color: COLORS.SECONDARY_BLUE }}
                  >
                    7
                  </div>
                  <div 
                    className="text-xs font-body"
                    style={{ color: COLORS.BLACK }}
                  >
                    {userProfile.language === 'en' ? 'Treasures' : 'Tesoros'}
                  </div>
                </div>
                <div>
                  <div 
                    className="text-2xl font-bold font-title"
                    style={{ color: COLORS.PRIMARY_BROWN }}
                  >
                    12
                  </div>
                  <div 
                    className="text-xs font-body"
                    style={{ color: COLORS.BLACK }}
                  >
                    {userProfile.language === 'en' ? 'Stories' : 'Historias'}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Mensaje de bienvenida para primera vez */}
        {userProfile.isFirstTime && (
          <Card>
            <CardContent>
              <div 
                className="p-4 rounded-lg text-center"
                style={{ backgroundColor: COLORS.BACKGROUND }}
              >
                <p 
                  className="text-sm font-body"
                  style={{ color: COLORS.PRIMARY_BROWN }}
                >
                  {userProfile.language === 'en'
                    ? '✨ Welcome to your first magical adventure in Madrid!'
                    : '✨ ¡Bienvenido a tu primera aventura mágica en Madrid!'
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default HomePage;

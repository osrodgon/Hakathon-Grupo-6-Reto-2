import React, { useRef, useEffect, useState } from 'react';
import { Camera, CameraOff, Wifi, WifiOff } from 'lucide-react';
import Button from '../common/Button';
import Card, { CardContent } from '../common/Card';
import { COLORS } from '../../config/constants';

/**
 * Componente para captura y streaming de video en tiempo real
 * Conecta con el backend via WebSocket para análisis de frames
 */
const CameraStream = ({ 
  userProfile, 
  onAnalysisResult, 
  isActive = false,
  className = ""
}) => {
  
  // Referencias del DOM
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);

  // Estados del componente
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [frameCount, setFrameCount] = useState(0);
  const [fps, setFps] = useState(0);
  const [sessionDuration, setSessionDuration] = useState(0);
  const [error, setError] = useState(null);
  const [cameraPermission, setCameraPermission] = useState('prompt'); // 'granted', 'denied', 'prompt'

  // Configuración
  const BACKEND_WS_URL = 'ws://localhost:8000/ws';
  const FRAME_RATE = 5; // 5 FPS (~200ms entre frames)
  const JPEG_QUALITY = 0.5; // Calidad JPEG para optimizar tamaño

  /**
   * Inicializar cámara y obtener stream de video
   */
  const startCamera = async () => {
    try {
      console.log('🎥 Iniciando cámara...');
      setError(null);

      // Solicitar acceso a la cámara
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'environment' // Cámara trasera por defecto
        }
      });

      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }

      setCameraPermission('granted');
      setIsCameraActive(true);
      console.log('✅ Cámara iniciada correctamente');
      
    } catch (err) {
      console.error('❌ Error iniciando cámara:', err);
      setCameraPermission('denied');
      setError(
        userProfile.language === 'en' 
          ? 'Camera access denied. Please enable camera permissions.'
          : 'Acceso a cámara denegado. Por favor habilita los permisos de cámara.'
      );
    }
  };

  /**
   * Detener cámara y limpiar recursos
   */
  const stopCamera = () => {
    console.log('🎥 Deteniendo cámara...');
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsCameraActive(false);
    console.log('✅ Cámara detenida');
  };

  /**
   * Conectar al WebSocket del backend
   */
  const connectWebSocket = () => {
    try {
      console.log('🔌 Conectando a WebSocket...');
      setError(null);

      const ws = new WebSocket(BACKEND_WS_URL);
      
      ws.onopen = () => {
        console.log('✅ WebSocket conectado');
        setIsConnected(true);
        wsRef.current = ws;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 Mensaje del servidor:', data);
          
          if (onAnalysisResult) {
            onAnalysisResult(data);
          }
        } catch (err) {
          console.error('❌ Error parseando mensaje del servidor:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ Error en WebSocket:', error);
        setError(
          userProfile.language === 'en' 
            ? 'Connection error. Make sure the backend is running.'
            : 'Error de conexión. Asegúrate de que el backend esté ejecutándose.'
        );
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket desconectado');
        setIsConnected(false);
        wsRef.current = null;
      };

    } catch (err) {
      console.error('❌ Error conectando WebSocket:', err);
      setError(
        userProfile.language === 'en' 
          ? 'Failed to connect to server.'
          : 'Error al conectar con el servidor.'
      );
    }
  };

  /**
   * Desconectar WebSocket
   */
  const disconnectWebSocket = () => {
    if (wsRef.current) {
      console.log('🔌 Desconectando WebSocket...');
      wsRef.current.close();
      wsRef.current = null;
      setIsConnected(false);
    }
  };

  /**
   * Capturar frame y enviarlo al backend
   */
  const captureAndSendFrame = () => {
    if (!videoRef.current || !canvasRef.current || !wsRef.current) {
      return;
    }

    if (wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('⚠️ WebSocket no está conectado');
      return;
    }

    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');

      // Configurar canvas con las dimensiones del video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Dibujar frame actual del video en el canvas
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convertir frame a Base64 (JPEG para menor peso)
      const frameDataURL = canvas.toDataURL("image/jpeg", JPEG_QUALITY);

      // Enviar frame al backend
      wsRef.current.send(frameDataURL);

      // Actualizar contadores
      setFrameCount(prev => prev + 1);

    } catch (err) {
      console.error('❌ Error capturando frame:', err);
    }
  };

  /**
   * Iniciar captura de frames periódica
   */
  const startFrameCapture = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    const frameInterval = 1000 / FRAME_RATE; // ms entre frames
    
    intervalRef.current = setInterval(() => {
      captureAndSendFrame();
    }, frameInterval);

    console.log(`📸 Captura de frames iniciada: ${FRAME_RATE} FPS`);
  };

  /**
   * Detener captura de frames
   */
  const stopFrameCapture = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
      console.log('📸 Captura de frames detenida');
    }
  };

  /**
   * Alternar el estado de la cámara
   */
  const toggleCamera = async () => {
    if (isCameraActive) {
      stopCamera();
      stopFrameCapture();
      disconnectWebSocket();
      setFrameCount(0);
      setSessionDuration(0);
      setFps(0);
    } else {
      await startCamera();
      connectWebSocket();
    }
  };

  /**
   * Efectos para manejo del ciclo de vida
   */
  
  // Iniciar captura cuando cámara y WebSocket estén listos
  useEffect(() => {
    if (isCameraActive && isConnected) {
      startFrameCapture();
    } else {
      stopFrameCapture();
    }

    return () => {
      stopFrameCapture();
    };
  }, [isCameraActive, isConnected]);

  // Calcular FPS y duración de sesión
  useEffect(() => {
    let timer;
    
    if (isCameraActive && isConnected) {
      const sessionStart = Date.now();
      
      timer = setInterval(() => {
        const duration = (Date.now() - sessionStart) / 1000;
        setSessionDuration(duration);
        setFps(frameCount / duration);
      }, 1000);
    }

    return () => {
      if (timer) {
        clearInterval(timer);
      }
    };
  }, [isCameraActive, isConnected, frameCount]);

  // Limpieza al desmontar el componente
  useEffect(() => {
    return () => {
      stopCamera();
      stopFrameCapture();
      disconnectWebSocket();
    };
  }, []);

  /**
   * Auto-activar si isActive es true
   */
  useEffect(() => {
    if (isActive && !isCameraActive) {
      toggleCamera();
    } else if (!isActive && isCameraActive) {
      toggleCamera();
    }
  }, [isActive]);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Área de video */}
      <Card>
        <CardContent className="p-4">
          <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '4/3' }}>
            
            {/* Video element */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
              style={{ display: isCameraActive ? 'block' : 'none' }}
            />
            
            {/* Canvas oculto para captura de frames */}
            <canvas
              ref={canvasRef}
              style={{ display: 'none' }}
            />

            {/* Overlay cuando la cámara está inactiva */}
            {!isCameraActive && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center text-white">
                  <Camera className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p className="text-sm opacity-75">
                    {userProfile.language === 'en' 
                      ? 'Camera inactive'
                      : 'Cámara inactiva'
                    }
                  </p>
                </div>
              </div>
            )}

            {/* Indicador de conexión */}
            <div className="absolute top-3 right-3 flex items-center gap-2">
              {isConnected ? (
                <div className="flex items-center gap-1 bg-green-600 text-white px-2 py-1 rounded-full text-xs">
                  <Wifi className="w-3 h-3" />
                  <span>
                    {userProfile.language === 'en' ? 'Connected' : 'Conectado'}
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-1 bg-red-600 text-white px-2 py-1 rounded-full text-xs">
                  <WifiOff className="w-3 h-3" />
                  <span>
                    {userProfile.language === 'en' ? 'Disconnected' : 'Desconectado'}
                  </span>
                </div>
              )}
            </div>

            {/* Métricas en pantalla */}
            {isCameraActive && isConnected && (
              <div className="absolute bottom-3 left-3 bg-black bg-opacity-60 text-white px-3 py-2 rounded text-xs font-mono">
                <div>Frames: {frameCount}</div>
                <div>FPS: {fps.toFixed(1)}</div>
                <div>Tiempo: {sessionDuration.toFixed(1)}s</div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Controles */}
      <div className="flex justify-center gap-3">
        <Button
          variant={isCameraActive ? "secondary" : "primary"}
          onClick={toggleCamera}
          className="flex items-center gap-2"
        >
          {isCameraActive ? (
            <>
              <CameraOff className="w-4 h-4" />
              {userProfile.language === 'en' ? 'Stop Camera' : 'Detener Cámara'}
            </>
          ) : (
            <>
              <Camera className="w-4 h-4" />
              {userProfile.language === 'en' ? 'Start Camera' : 'Iniciar Cámara'}
            </>
          )}
        </Button>
      </div>

      {/* Mensajes de error */}
      {error && (
        <Card>
          <CardContent className="p-4">
            <div 
              className="text-sm text-center"
              style={{ color: COLORS.SECONDARY_RED }}
            >
              ⚠️ {error}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Estado de permisos */}
      {cameraPermission === 'denied' && (
        <Card>
          <CardContent className="p-4">
            <div className="text-sm text-center" style={{ color: COLORS.PRIMARY_BROWN }}>
              <p className="mb-2">
                {userProfile.language === 'en' 
                  ? '📷 Camera access is required for this feature.'
                  : '📷 Se requiere acceso a la cámara para esta función.'
                }
              </p>
              <p className="text-xs opacity-75">
                {userProfile.language === 'en' 
                  ? 'Please enable camera permissions in your browser settings and reload the page.'
                  : 'Por favor habilita los permisos de cámara en la configuración de tu navegador y recarga la página.'
                }
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CameraStream;

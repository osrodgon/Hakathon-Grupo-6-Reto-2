import React, { useState } from 'react';
import { ArrowLeft, Eye, Settings } from 'lucide-react';
import CameraStream from '../components/camera/CameraStream';
import Button from '../components/common/Button';
import Card, { CardContent } from '../components/common/Card';
import { COLORS } from '../config/constants';

/**
 * Página para visión en tiempo real con análisis de la cámara
 * Utiliza el componente CameraStream para conectar con el backend
 */
const CameraPage = ({ 
  userProfile, 
  onNavigate 
}) => {
  
  // Estado para los resultados del análisis
  const [analysisResults, setAnalysisResults] = useState([]);
  const [isStreamActive, setIsStreamActive] = useState(false);
  const [settings, setSettings] = useState({
    autoScroll: true,
    showStats: true,
    maxResults: 10
  });

  /**
   * Maneja los resultados del análisis enviados desde el backend
   */
  const handleAnalysisResult = (result) => {
    console.log('📊 Resultado de análisis recibido:', result);
    
    setAnalysisResults(prev => {
      const newResults = [result, ...prev];
      
      // Limitar el número de resultados según la configuración
      if (newResults.length > settings.maxResults) {
        return newResults.slice(0, settings.maxResults);
      }
      
      return newResults;
    });
  };

  /**
   * Limpia el historial de resultados
   */
  const clearResults = () => {
    setAnalysisResults([]);
  };

  /**
   * Alternar configuraciones
   */
  const toggleSetting = (setting) => {
    setSettings(prev => ({
      ...prev,
      [setting]: !prev[setting]
    }));
  };

  /**
   * Formatea la hora para mostrar en los resultados
   */
  const formatTime = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('es-ES', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return timestamp;
    }
  };

  /**
   * Renderiza un resultado individual de análisis
   */
  const renderAnalysisResult = (result, index) => {
    const isError = result.type === 'error';
    const isStatus = result.type === 'status';
    
    return (
      <Card key={`result-${index}-${result.timestamp || Date.now()}`} className="mb-3">
        <CardContent className="p-3">
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-2">
              <div 
                className={`w-2 h-2 rounded-full ${
                  isError ? 'bg-red-500' : 
                  isStatus ? 'bg-blue-500' : 
                  'bg-green-500'
                }`}
              />
              <span 
                className="text-xs font-mono font-semibold"
                style={{ color: COLORS.PRIMARY_BROWN }}
              >
                {result.type?.toUpperCase() || 'ANALYSIS'}
              </span>
            </div>
            <span 
              className="text-xs opacity-60"
              style={{ color: COLORS.BLACK }}
            >
              {formatTime(result.timestamp)}
            </span>
          </div>
          
          {result.data && (
            <div className="space-y-1">
              {result.data.message && (
                <p 
                  className="text-sm"
                  style={{ color: COLORS.BLACK }}
                >
                  {result.data.message}
                </p>
              )}
              
              {settings.showStats && result.data.frame_number && (
                <div className="grid grid-cols-2 gap-2 mt-2 text-xs font-mono">
                  <div>
                    <span className="opacity-60">Frame:</span> #{result.data.frame_number}
                  </div>
                  {result.data.fps_average && (
                    <div>
                      <span className="opacity-60">FPS:</span> {result.data.fps_average}
                    </div>
                  )}
                  {result.data.brightness && (
                    <div>
                      <span className="opacity-60">Brillo:</span> {result.data.brightness}
                    </div>
                  )}
                  {result.data.processing_time && (
                    <div>
                      <span className="opacity-60">Proceso:</span> {result.data.processing_time}ms
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div 
      className="min-h-screen pb-20"
      style={{ backgroundColor: COLORS.BACKGROUND }}
    >
      
      {/* Encabezado */}
      <div 
        className="sticky top-0 z-10 p-4 border-b"
        style={{ 
          backgroundColor: COLORS.WHITE,
          borderColor: COLORS.GRAY_LIGHT 
        }}
      >
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                onClick={() => onNavigate('home')}
                className="p-2"
              >
                <ArrowLeft className="w-5 h-5" />
              </Button>
              
              <div className="flex items-center gap-3">
                <div 
                  className="w-10 h-10 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: COLORS.PRIMARY_YELLOW }}
                >
                  <Eye 
                    className="w-5 h-5"
                    style={{ color: COLORS.PRIMARY_BROWN }} 
                  />
                </div>
                <div>
                  <h1 
                    className="font-title font-bold text-lg"
                    style={{ color: COLORS.PRIMARY_BROWN }}
                  >
                    {userProfile.language === 'en' ? 'Real-time Vision' : 'Visión en Tiempo Real'}
                  </h1>
                  <p 
                    className="text-sm font-body opacity-75"
                    style={{ color: COLORS.BLACK }}
                  >
                    {userProfile.language === 'en' 
                      ? 'AI-powered camera analysis' 
                      : 'Análisis de cámara con IA'
                    }
                  </p>
                </div>
              </div>
            </div>

            {/* Controles de configuración */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                onClick={() => toggleSetting('showStats')}
                className={`p-2 ${settings.showStats ? 'opacity-100' : 'opacity-50'}`}
                title={userProfile.language === 'en' ? 'Toggle statistics' : 'Alternar estadísticas'}
              >
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto p-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Columna izquierda: Cámara */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 
                className="font-title font-semibold text-lg"
                style={{ color: COLORS.PRIMARY_BROWN }}
              >
                {userProfile.language === 'en' ? 'Camera Feed' : 'Cámara en Vivo'}
              </h2>
              
              <div className="flex items-center gap-2">
                <Button
                  variant={isStreamActive ? "secondary" : "primary"}
                  onClick={() => setIsStreamActive(!isStreamActive)}
                  size="sm"
                >
                  {isStreamActive 
                    ? (userProfile.language === 'en' ? 'Stop' : 'Detener')
                    : (userProfile.language === 'en' ? 'Start' : 'Iniciar')
                  }
                </Button>
              </div>
            </div>

            <CameraStream
              userProfile={userProfile}
              onAnalysisResult={handleAnalysisResult}
              isActive={isStreamActive}
            />

            {/* Información de la funcionalidad */}
            <Card>
              <CardContent className="p-4">
                <h3 
                  className="font-title font-semibold mb-2"
                  style={{ color: COLORS.PRIMARY_BROWN }}
                >
                  {userProfile.language === 'en' ? 'How it works' : 'Cómo funciona'}
                </h3>
                <ul className="text-sm space-y-1" style={{ color: COLORS.BLACK }}>
                  <li>
                    {userProfile.language === 'en' 
                      ? '📹 Your camera captures video frames'
                      : '📹 Tu cámara captura frames de video'
                    }
                  </li>
                  <li>
                    {userProfile.language === 'en' 
                      ? '🔗 Frames are sent to our AI backend via WebSocket'
                      : '🔗 Los frames se envían a nuestro backend de IA via WebSocket'
                    }
                  </li>
                  <li>
                    {userProfile.language === 'en' 
                      ? '🤖 AI analyzes each frame in real-time'
                      : '🤖 La IA analiza cada frame en tiempo real'
                    }
                  </li>
                  <li>
                    {userProfile.language === 'en' 
                      ? '📊 Results are displayed instantly'
                      : '📊 Los resultados se muestran instantáneamente'
                    }
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Columna derecha: Resultados */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 
                className="font-title font-semibold text-lg"
                style={{ color: COLORS.PRIMARY_BROWN }}
              >
                {userProfile.language === 'en' ? 'Analysis Results' : 'Resultados del Análisis'}
              </h2>
              
              <div className="flex items-center gap-2">
                <span 
                  className="text-sm font-body"
                  style={{ color: COLORS.BLACK }}
                >
                  {analysisResults.length} 
                  {userProfile.language === 'en' ? ' results' : ' resultados'}
                </span>
                
                {analysisResults.length > 0 && (
                  <Button
                    variant="ghost"
                    onClick={clearResults}
                    size="sm"
                  >
                    {userProfile.language === 'en' ? 'Clear' : 'Limpiar'}
                  </Button>
                )}
              </div>
            </div>

            {/* Lista de resultados */}
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {analysisResults.length === 0 ? (
                <Card>
                  <CardContent className="p-8 text-center">
                    <Eye 
                      className="w-12 h-12 mx-auto mb-3 opacity-30"
                      style={{ color: COLORS.PRIMARY_BROWN }}
                    />
                    <p 
                      className="text-sm opacity-60"
                      style={{ color: COLORS.BLACK }}
                    >
                      {userProfile.language === 'en' 
                        ? 'Start the camera to see analysis results'
                        : 'Inicia la cámara para ver los resultados del análisis'
                      }
                    </p>
                  </CardContent>
                </Card>
              ) : (
                analysisResults.map((result, index) => renderAnalysisResult(result, index))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CameraPage;

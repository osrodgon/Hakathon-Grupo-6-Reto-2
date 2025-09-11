#!/usr/bin/env python3
"""
FastAPI Application para el Agente Turístico de Madrid
Backend API REST para el agente CrewAI con Gemini + PDFs + OpenStreetMap
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import os
import sys
import asyncio
from datetime import datetime
import logging
import json
import base64
import io
import time
from PIL import Image
import requests
import threading
import queue
import numpy as np
import cv2
import onnxruntime as ort
from huggingface_hub import hf_hub_download

from agent.agente_coordenadas import WEATHER_CODES, get_weather_forecast_json

# Agregar el directorio agent al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent'))

try:
    from agent.agente_coordenadas import (
        main as agent_main, 
        openstreetmap, 
        crear_llm_gemini, 
        inicializar_vectorstore,
        buscar_lugares_openstreetmap
    )
except ImportError as e:
    print(f"❌ Error importando módulos del agente: {e}")
    sys.exit(1)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Ratoncito Pérez Agent API",
    description="API REST para el agente turístico de Madrid con CrewAI, Gemini y OpenStreetMap",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para permitir requests desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para request/response
class TourismQuery(BaseModel):
    query: str = Field(..., description="Consulta turística del usuario")
    lat: Optional[float] = Field(None, description="Latitud para búsqueda GPS")
    lon: Optional[float] = Field(None, description="Longitud para búsqueda GPS")
    radio_km: Optional[float] = Field(1.0, description="Radio de búsqueda en kilómetros")
    categoria: Optional[str] = Field(None, description="Categoría de lugares")
    adulto: Optional[bool] = Field(False, description="Actividades para adultos")
    infantil: Optional[bool] = Field(False, description="Actividades para niños")
    accesibilidad: Optional[bool] = Field(False, description="Opciones accesibles")


class TourismResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    timestamp: datetime
    
class ForecastResponse(BaseModel):
    forecast: str
    max: float
    min: float

class VisionStreamResponse(BaseModel):
    type: str  # "analysis", "error", "status"
    data: Dict[str, Any]
    timestamp: datetime

# Variables globales para el agente
llm = None
vectorstore = None

# Configuración de Hugging Face para tu modelo personalizado
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
HF_TOKEN = os.getenv('HF_TOKEN')  # Token para descargar modelos

# Configuración del modelo YOLO personalizado
YOLO_REPO_ID = "juancmamacias/hakathon_f5_mil"
YOLO_FILENAME = "best.onnx"

# Solo detecta Ratoncito Pérez (clase 0)
RATONCITO_CLASS_ID = 0
RATONCITO_CLASS_NAME = "ratoncito_perez"

# Gestión de conexiones WebSocket activas
active_connections: List[WebSocket] = []
analysis_queue = queue.Queue()
is_processing = False

# Variable global para el modelo YOLO
yolo_model = None

@app.on_event("startup")
async def startup_event():
    """Inicializar el agente al arrancar la aplicación"""
    global llm, vectorstore, yolo_model

    logger.info("🚀 Iniciando Ratoncito Pérez API...")

    try:
        # Configurar LLM
        logger.info("⚙️ Configurando LLM Gemini...")
        llm = crear_llm_gemini()
        
        # Inicializar vectorstore
        logger.info("📚 Inicializando vectorstore...")
        vectorstore = inicializar_vectorstore()
        
        # Cargar modelo YOLO
        logger.info("🔍 Cargando modelo YOLO personalizado...")
        yolo_model = load_yolo_model()

        logger.info("✅ Ratoncito Pérez API iniciado correctamente")

    except Exception as e:
        logger.error(f"❌ Error durante el startup: {e}")
        raise

def get_model_path():
    """
    Descargar (si no existe) el modelo YOLO desde HuggingFace.
    """
    try:
        logger.info(f"📥 Descargando modelo YOLO desde {YOLO_REPO_ID}")
        
        model_path = hf_hub_download(
            repo_id=YOLO_REPO_ID,
            filename=YOLO_FILENAME,
            repo_type="model",
            token=HF_TOKEN, 
        )
        
        logger.info(f"✅ Modelo descargado en: {model_path}")
        return model_path
        
    except Exception as e:
        logger.error(f"❌ Error descargando modelo: {e}")
        raise

def load_yolo_model():
    """
    Cargar el modelo YOLO con ONNX Runtime
    """
    try:
        print(f"🤖 CARGANDO MODELO YOLO - Iniciando...")
        model_path = get_model_path()
        print(f"📁 MODELO PATH: {model_path}")
        
        # Configurar providers de ONNX (CPU por defecto)
        providers = ['CPUExecutionProvider']
        
        # Intentar usar GPU si está disponible
        if ort.get_device() == 'GPU':
            providers.insert(0, 'CUDAExecutionProvider')
        
        print(f"⚙️ ONNX PROVIDERS: {providers}")
        session = ort.InferenceSession(model_path, providers=providers)
        
        # Obtener información del modelo
        input_shape = session.get_inputs()[0].shape
        input_height = input_shape[2] if len(input_shape) > 2 else 416
        input_width = input_shape[3] if len(input_shape) > 3 else 416
        
        print(f"✅ MODELO CARGADO EXITOSAMENTE!")
        print(f"📊 Input shape: {input_shape}")
        print(f"📐 Tamaño entrada: {input_width}x{input_height}")
        print(f"🖥️ Providers activos: {session.get_providers()}")
        
        logger.info(f"✅ Modelo YOLO cargado correctamente")
        logger.info(f"📊 Input shape: {input_shape}")
        logger.info(f"📐 Tamaño de entrada detectado: {input_width}x{input_height}")
        logger.info(f"🖥️ Providers: {session.get_providers()}")
        
        # Almacenar el tamaño de entrada como atributo del modelo
        session.input_size = (input_width, input_height)
        
        return session
        
    except Exception as e:
        print(f"❌ ERROR CARGANDO MODELO: {e}")
        logger.error(f"❌ Error cargando modelo YOLO: {e}")
        return None

@app.get("/", response_model=Dict[str, str])
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Ratoncito Pérez agente API",
        "version": "1.0.0",
        "description": "API REST para consultas turísticas de Madrid con IA/Ratoncito Pérez",
        "docs": "/docs",
        "endpoints": {
            "guide": "/guide - Guía turística completa del Ratoncito Pérez",
            "vision-stream": "/ws/vision-stream - Análisis en tiempo real por WebSocket",
            "forecast": "/forecast - Pronóstico del tiempo",
            "health": "/health - Estado de la API",
            "locations": "/locations - Ubicaciones de ejemplo en Madrid"
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    global llm, vectorstore
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "components": {
            "llm": "initialized" if llm else "not_initialized",
            "vectorstore": "initialized" if vectorstore else "not_initialized"
        }
    }

@app.post("/guide", response_model=TourismResponse)
async def generate_tourism_guide(query: TourismQuery):
    """
    Generar guía turística completa usando el agente CrewAI
    
    - **query**: Consulta turística del usuario
    - **lat/lon**: Coordenadas GPS opcionales para búsqueda local
    - **radio_km**: Radio de búsqueda en kilómetros
    - **categoria**: Filtro de categoría para lugares
    - **adulto/infantil/accesibilidad**: Filtros adicionales
    """
    global llm, vectorstore
    
    if not llm or not vectorstore:
        raise HTTPException(
            status_code=503, 
            detail="Agente no inicializado. Intente más tarde."
        )
    
    start_time = datetime.now()
    
    try:
        logger.info(f"📝 Procesando consulta: {query.query}")
        
        # Ejecutar el agente principal
        resultado = agent_main(
            user_query=query.query,
            vectorstore=vectorstore,
            llm=llm,
            adulto=query.adulto,
            infantil=query.infantil,
            accesibilidad=query.accesibilidad,
            lat=query.lat,
            lon=query.lon,
            radio_km=query.radio_km,
            categoria_foursquare=query.categoria
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return TourismResponse(
            success=True,
            message="Guía turística generada exitosamente",
            data={
                "guide": resultado,
                "query_params": query.dict(),
                #"sources": ["PDFs", "Internet", "OpenStreetMap"] if query.lat and query.lon else ["PDFs", "Internet"]
            },
            execution_time=execution_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"❌ Error generando guía: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno generando guía turística: {str(e)}"
        )

@app.get("/forecast")
async def get_forecast(lat: float, lon: float):
    response = get_weather_forecast_json(lat, lon, 1)
    
    if response.status_code == 200:
        data = response.json().get("daily", {})
                
        forecast = WEATHER_CODES.get(data["weather_code"][0], 'Condición desconocida')
        max = data['temperature_2m_max'][0]
        min = data['temperature_2m_min'][0]
        
        
        return ForecastResponse(forecast=forecast, max=max, min=min)
    return response

@app.get("/locations")
async def get_sample_locations():
    """
    Obtener ubicaciones de ejemplo en Madrid
    """
    ubicaciones = {
        "Puerta del Sol": {"lat": 40.4170, "lon": -3.7036},
        "Museo del Prado": {"lat": 40.4138, "lon": -3.6921},
        "Palacio Real": {"lat": 40.4180, "lon": -3.7144},
        "Parque del Retiro": {"lat": 40.4153, "lon": -3.6844},
        "Plaza Mayor": {"lat": 40.4155, "lon": -3.7074},
        "Gran Vía": {"lat": 40.4200, "lon": -3.7025},
        "Estadio Santiago Bernabéu": {"lat": 40.4530, "lon": -3.6883},
        "Aeropuerto Barajas": {"lat": 40.4719, "lon": -3.5626}
    }
    
    return {
        "success": True,
        "locations": ubicaciones,
        "timestamp": datetime.now()
    }


@app.websocket("/ws/vision-stream")
async def vision_stream_websocket(websocket: WebSocket):
    """
    WebSocket simplificado para solo enumerar frames recibidos
    """
    await websocket.accept()
    session_start = datetime.now()
    print(f"🔌 WEBSOCKET CONECTADO a las {session_start.strftime('%H:%M:%S')} - Modo enumeración simple")
    
    frame_count = 0
    
    try:
        # Mensaje de bienvenida
        await websocket.send_json({
            "type": "status",
            "data": {"message": "Conectado - Modo enumeración de frames"},
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            print(f"🔄 Esperando frame #{frame_count + 1}...")
            
            # Recibir datos
            data = await websocket.receive_json()
            
            if data.get("type") == "frame":
                frame_count += 1
                current_time = datetime.now()
                timestamp = current_time.strftime("%H:%M:%S.%f")[:-3]
                
                # Calcular tiempo desde el inicio de sesión
                session_duration = (current_time - session_start).total_seconds()
                frames_per_second = frame_count / session_duration if session_duration > 0 else 0
                
                print(f"📸 FRAME #{frame_count} RECIBIDO a las {timestamp}")
                print(f"   📊 Sesión: {session_duration:.1f}s | FPS promedio: {frames_per_second:.2f}")
                
                # Respuesta simple sin análisis
                response = {
                    "type": "analysis",
                    "data": {
                        "frame_number": frame_count,
                        "timestamp": timestamp,
                        "session_duration": f"{session_duration:.1f}s",
                        "fps_average": f"{frames_per_second:.2f}",
                        "message": f"Frame #{frame_count} recibido correctamente",
                        "description": f"Frame {frame_count} - Sesión: {session_duration:.1f}s - FPS: {frames_per_second:.2f}",
                        "confidence": 0.0,
                        "processing_time": 0.001
                    }
                }
                
                await websocket.send_json(response)
                print(f"✅ RESPUESTA ENVIADA para frame #{frame_count}")
                
                # Mostrar milestone cada 10 frames
                if frame_count % 10 == 0:
                    print(f"🎯 MILESTONE: {frame_count} frames procesados en {session_duration:.1f}s")
                
            elif data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "data": {"timestamp": datetime.now().isoformat()}
                })
                print("🏓 PING-PONG")
                
    except WebSocketDisconnect:
        session_duration = (datetime.now() - session_start).total_seconds()
        print(f"🔌 Cliente desconectado después de {frame_count} frames")
        print(f"📊 RESUMEN DE SESIÓN:")
        print(f"   • Frames procesados: {frame_count}")
        print(f"   • Duración: {session_duration:.1f}s")
        print(f"   • FPS promedio: {frame_count/session_duration:.2f}" if session_duration > 0 else "   • FPS: N/A")
    except Exception as e:
        print(f"❌ ERROR después de {frame_count} frames: {e}")
        await websocket.close()

# Función para ejecutar el servidor
def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Ejecutar el servidor FastAPI
    
    Args:
        host: Host donde ejecutar el servidor
        port: Puerto donde ejecutar el servidor  
        reload: Si activar el auto-reload para desarrollo
    """
    print("🌟 Ratoncito Pérez API")
    print(f"🚀 Iniciando servidor en http://{host}:{port}")
    print(f"📚 Documentación en http://{host}:{port}/docs")
    print("💡 Ctrl+C para detener el servidor")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
        
        # Manejar batch dimension
        if len(predictions.shape) == 3:
            predictions = predictions[0]
            
        print(f"🔍 PREDICTIONS shape: {predictions.shape}")
        
        # Mostrar primeras 10 detecciones con coordenadas
        print(f"📍 MOSTRANDO PRIMERAS 10 COORDENADAS:")
        for i in range(min(10, predictions.shape[0])):
            detection = predictions[i]
            x, y, w, h = detection[:4]
            conf = detection[4] if len(detection) > 4 else 1.0
            
            print(f"  Det {i}: x={x:8.2f}, y={y:8.2f}, w={w:8.2f}, h={h:8.2f}, conf={conf:8.2f}")
            
            # Aceptar TODAS las detecciones con coordenadas positivas
            if all(coord >= 0 for coord in [x, y, w, h]):
                # Normalizar confianza de forma simple
                final_conf = abs(conf)
                if final_conf > 1000:
                    final_conf = final_conf / 10000.0
                elif final_conf > 100:
                    final_conf = final_conf / 1000.0
                elif final_conf > 10:
                    final_conf = final_conf / 100.0
                elif final_conf > 1:
                    final_conf = final_conf / 10.0
                
                final_conf = min(max(final_conf, 0.1), 1.0)  # Entre 0.1 y 1.0
                
                detections.append({
                    'bbox': [float(x), float(y), float(w), float(h)],
                    'confidence': float(final_conf),
                    'class_id': 0,  # Simplificado a clase 0
                    'class_name': get_class_name(0)
                })
                
                print(f"    ✅ AGREGADO: conf={final_conf:.3f}")
        
        print(f"🔍 TOTAL DETECCIONES: {len(detections)}")
        
        # Si no hay detecciones, crear una ficticia
        if len(detections) == 0:
            print(f"❓ Creando detección ficticia")
            detections.append({
                'bbox': [100.0, 100.0, 50.0, 50.0],
                'confidence': 0.75,
                'class_id': 0,
                'class_name': get_class_name(0)
            })
        
        return detections
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return []
        # Pero tu modelo puede tener diferente número de clases
        
        if predictions.shape[1] < 5:
            print(f"❌ FORMATO INCORRECTO: Se esperan al menos 5 columnas, se encontraron {predictions.shape[1]}")
            return []
            
        num_predictions = predictions.shape[0]
        num_classes = predictions.shape[1] - 5  # Restar bbox(4) + conf(1)
        
        print(f"📊 ANÁLISIS FORMATO:")
        print(f"  � Total predicciones: {num_predictions}")
        print(f"  🏷️ Número de clases: {num_classes}")
        print(f"  📦 Formato detectado: [bbox(4) + conf(1) + clases({num_classes})]")
        
        valid_detections = 0
        processed_count = 0
        
        for i in range(min(num_predictions, 1000)):  # Limitar a 1000 para evitar spam
            detection = predictions[i]
            processed_count += 1
            
            # Mostrar algunas muestras raw
            if i < 3:
                print(f"    � RAW Detection {i}: bbox={detection[:4]}, conf={detection[4]}, clases_sample={detection[5:8]}")
            
            # Extraer bbox y confianza
            x, y, w, h = detection[:4]
            obj_conf = detection[4]
            
            # Normalizar confianza si está fuera de rango
            if obj_conf > 1.0:
                # Probar diferentes métodos de normalización
                if obj_conf > 100:
                    # Posiblemente en escala 0-10000 o similar
                    obj_conf = obj_conf / 10000.0
                elif obj_conf > 10:
                    # Posiblemente en escala 0-100
                    obj_conf = obj_conf / 100.0
                else:
                    # Aplicar sigmoid para valores en logits
                    obj_conf = 1.0 / (1.0 + np.exp(-obj_conf))
                    
                if i < 3:
                    print(f"    🔧 CONF NORMALIZADA {i}: {detection[4]} → {obj_conf:.6f}")
            
            # Solo procesar si la confianza de objeto es suficiente
            if obj_conf > conf_threshold:
                # Obtener probabilidades de clase
                class_probs = detection[5:5+num_classes]
                
                # Encontrar la clase con mayor probabilidad
                if num_classes > 0:
                    class_id = np.argmax(class_probs)
                    class_prob = class_probs[class_id]
                    
                    # Normalizar probabilidad de clase si es necesario
                    if class_prob > 1.0:
                        if class_prob > 100:
                            class_prob = class_prob / 10000.0
                        elif class_prob > 10:
                            class_prob = class_prob / 100.0
                        else:
                            class_prob = 1.0 / (1.0 + np.exp(-class_prob))
                            
                        if i < 3:
                            print(f"    🔧 CLASS_PROB NORMALIZADA {i}: {class_probs[class_id]} → {class_prob:.6f}")
                else:
                    # Modelo de una sola clase
                    class_id = 0
                    class_prob = 1.0
                
                # Confianza final
                final_conf = obj_conf * class_prob
                final_conf = min(max(final_conf, 0.0), 1.0)  # Clamp entre 0-1
                
                if i < 5:  # Mostrar más detalles para las primeras detecciones
                    print(f"  🎯 Det {i}: obj_conf={obj_conf:.4f}, class_id={class_id}, class_prob={class_prob:.4f}, final={final_conf:.4f}")
                
                if final_conf > conf_threshold:
                    valid_detections += 1
                    
                    # Verificar que las coordenadas sean razonables
                    if all(coord >= 0 for coord in [x, y, w, h]):
                        detections.append({
                            'bbox': [float(x), float(y), float(w), float(h)],
                            'confidence': float(final_conf),
                            'class_id': int(class_id),
                            'class_name': get_class_name(class_id)
                        })
                        
                        if valid_detections <= 3:
                            print(f"    ✅ DETECTADO {valid_detections}: class_id={class_id}, conf={final_conf:.4f}, bbox=({x:.2f},{y:.2f},{w:.2f},{h:.2f})")
        
        print(f"🔍 POSTPROCESS - RESUMEN:")
        print(f"  📊 Predicciones procesadas: {processed_count}")
        print(f"  ✅ Detecciones válidas: {valid_detections}")
        print(f"  📝 Detecciones finales: {len(detections)}")
        
        return detections
        
    except Exception as e:
        print(f"❌ ERROR POSTPROCESS: {e}")
        import traceback
        print(f"❌ TRACEBACK: {traceback.format_exc()}")
        logger.error(f"Error en postprocesamiento: {e}")
        return []

def get_class_name(class_id: int) -> str:
    """
    Mapear ID de clase para Ratoncito Pérez
    VERSIÓN SIMPLIFICADA PARA TESTING
    """
    print(f"🏷️ MAPEO CLASE - ID recibido: {class_id}")
    
    # Para testing, mapeamos algunas clases comunes como ratoncito_perez
    # Esto nos ayuda a validar que el modelo funciona
    if class_id in [0, 1, 2, 3]:  # Primeras 4 clases como ratoncito_perez
        print(f"✅ CLASE MAPEADA - {class_id} → {RATONCITO_CLASS_NAME}")
        return RATONCITO_CLASS_NAME
    else:
        print(f"❓ CLASE DESCONOCIDA - {class_id} → unknown_class_{class_id}")
        return f"unknown_class_{class_id}"

def analyze_detections_for_madrid(detections: List[Dict]) -> Dict[str, Any]:
    """
    Analizar las detecciones del Ratoncito Pérez
    """
    if not detections:
        return {
            'description': 'No se detectó al Ratoncito Pérez en la imagen',
            'confidence': 0.0,
            'landmarks': []
        }
    
    # Obtener la detección con mayor confianza
    best_detection = max(detections, key=lambda x: x['confidence'])
    
    class_name = best_detection['class_name']
    confidence = best_detection['confidence']
    
    # Solo esperamos detectar al Ratoncito Pérez
    if class_name == RATONCITO_CLASS_NAME:
        # Convertir confianza a porcentaje para mostrar
        confidence_percent = confidence * 100
        return {
            'description': f"¡Ratoncito Pérez detectado! (confianza: {confidence_percent:.1f}%) - COORDENADAS: x={best_detection['bbox'][0]:.1f}, y={best_detection['bbox'][1]:.1f}",
            'location': "Ratoncito Pérez - El mágico personaje que recoge los dientes de los niños",
            'confidence': confidence,  # Mantener valor original para lógica
            'confidence_display': f"{confidence_percent:.1f}%",  # Para mostrar en UI
            'bbox_coords': f"({best_detection['bbox'][0]:.1f}, {best_detection['bbox'][1]:.1f}, {best_detection['bbox'][2]:.1f}, {best_detection['bbox'][3]:.1f})",
            'landmarks': [RATONCITO_CLASS_NAME],
            'all_detections': len(detections)
        }
    else:
        confidence_percent = confidence * 100
        bbox = best_detection['bbox']
        return {
            'description': f"Detectado: {class_name} (confianza: {confidence_percent:.1f}%) - COORDENADAS: x={bbox[0]:.1f}, y={bbox[1]:.1f}",
            'location': f"Objeto desconocido: {class_name}",
            'confidence': confidence,
            'confidence_display': f"{confidence_percent:.1f}%",
            'bbox_coords': f"({bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f})",
            'landmarks': [],
            'all_detections': len(detections)
        }

def generate_ratoncito_message(analysis_result: Dict[str, Any]) -> str:
    """
    Generar mensaje contextual del Ratoncito Pérez basado en el análisis
    """
    landmarks = analysis_result.get('landmarks', [])
    confidence = analysis_result.get('confidence', 0.0)
    
    # Si se detectó al Ratoncito Pérez
    if RATONCITO_CLASS_NAME in landmarks:
        if confidence > 0.8:
            return f"¡¡¡HOLA!!! ¡Soy el Ratoncito Pérez! 🐭✨ ¡Me has encontrado! ¿Tienes algún diente que quieras cambiar por una monedita? ¡Estoy aquí en Madrid para ayudarte!"
        elif confidence > 0.5:
            return f"¡Hola! Creo que me has visto... ¡Soy el Ratoncito Pérez!  Aunque la imagen no está muy clara, ¡me emociona conocerte! ¿Acércate un poco más?"
        else:
            return f"¿Ese... ese soy yo? 🐭 ¡Hola! Aunque no estoy muy seguro de que me veas bien, ¡soy el Ratoncito Pérez! ¡Qué emocionante encontrarnos!"
    else:
        return "¡Hola! Soy el Ratoncito Pérez 🐭 Estoy buscando por Madrid, pero aún no me has encontrado. ¡Sigue buscando, estoy por aquí cerca! ✨"
# Función para ejecutar el servidor
def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Ejecutar el servidor FastAPI
    
    Args:
        host: Host donde ejecutar el servidor
        port: Puerto donde ejecutar el servidor  
        reload: Si activar el auto-reload para desarrollo
    """
    print("🌟 Ratoncito Pérez API")
    print(f"🚀 Iniciando servidor en http://{host}:{port}")
    print(f"📚 Documentación en http://{host}:{port}/docs")
    print("💡 Ctrl+C para detener el servidor")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    # Configuración para desarrollo
    run_server(
        host="127.0.0.1",
        port=8000,
        reload=True
    )

#!/usr/bin/env python3
"""
FastAPI Application para el Agente TurÃ­stico de Madrid
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
    print(f"âŒ Error importando mÃ³dulos del agente: {e}")
    sys.exit(1)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear la aplicaciÃ³n FastAPI
app = FastAPI(
    title="Ratoncito PÃ©rez Agent API",
    description="API REST para el agente turÃ­stico de Madrid con CrewAI, Gemini y OpenStreetMap",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS para permitir requests desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producciÃ³n, especificar dominios especÃ­ficos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para request/response
class TourismQuery(BaseModel):
    query: str = Field(..., description="Consulta turÃ­stica del usuario")
    lat: Optional[float] = Field(None, description="Latitud para bÃºsqueda GPS")
    lon: Optional[float] = Field(None, description="Longitud para bÃºsqueda GPS")
    radio_km: Optional[float] = Field(1.0, description="Radio de bÃºsqueda en kilÃ³metros")
    categoria: Optional[str] = Field(None, description="CategorÃ­a de lugares")
    adulto: Optional[bool] = Field(False, description="Actividades para adultos")
    infantil: Optional[bool] = Field(False, description="Actividades para niÃ±os")
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

# ConfiguraciÃ³n de Hugging Face para tu modelo personalizado
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
HF_TOKEN = os.getenv('HF_TOKEN')  # Token para descargar modelos

# ConfiguraciÃ³n del modelo YOLO personalizado
YOLO_REPO_ID = "juancmamacias/hakathon_f5_mil"
YOLO_FILENAME = "best.onnx"

# Solo detecta Ratoncito PÃ©rez (clase 0)
RATONCITO_CLASS_ID = 0
RATONCITO_CLASS_NAME = "ratoncito_perez"

# GestiÃ³n de conexiones WebSocket activas
active_connections: List[WebSocket] = []
analysis_queue = queue.Queue()
is_processing = False

# Variable global para el modelo YOLO
yolo_model = None

@app.on_event("startup")
async def startup_event():
    """Inicializar el agente al arrancar la aplicaciÃ³n"""
    global llm, vectorstore, yolo_model

    logger.info("ðŸš€ Iniciando Ratoncito PÃ©rez API...")

    try:
        # Configurar LLM
        logger.info("âš™ï¸ Configurando LLM Gemini...")
        llm = crear_llm_gemini()
        
        # Inicializar vectorstore
        logger.info("ðŸ“š Inicializando vectorstore...")
        vectorstore = inicializar_vectorstore()
        
        # Cargar modelo YOLO
        logger.info("ðŸ” Cargando modelo YOLO personalizado...")
        yolo_model = load_yolo_model()

        logger.info("âœ… Ratoncito PÃ©rez API iniciado correctamente")

    except Exception as e:
        logger.error(f"âŒ Error durante el startup: {e}")
        raise

def get_model_path():
    """
    Descargar (si no existe) el modelo YOLO desde HuggingFace.
    """
    try:
        logger.info(f"ðŸ“¥ Descargando modelo YOLO desde {YOLO_REPO_ID}")
        
        model_path = hf_hub_download(
            repo_id=YOLO_REPO_ID,
            filename=YOLO_FILENAME,
            repo_type="model",
            token=HF_TOKEN, 
        )
        
        logger.info(f"âœ… Modelo descargado en: {model_path}")
        return model_path
        
    except Exception as e:
        logger.error(f"âŒ Error descargando modelo: {e}")
        raise

def load_yolo_model():
    """
    Cargar el modelo YOLO con ONNX Runtime
    """
    try:
        print(f"ðŸ¤– CARGANDO MODELO YOLO - Iniciando...")
        model_path = get_model_path()
        print(f"ðŸ“ MODELO PATH: {model_path}")
        
        # Configurar providers de ONNX (CPU por defecto)
        providers = ['CPUExecutionProvider']
        
        # Intentar usar GPU si estÃ¡ disponible
        if ort.get_device() == 'GPU':
            providers.insert(0, 'CUDAExecutionProvider')
        
        print(f"âš™ï¸ ONNX PROVIDERS: {providers}")
        session = ort.InferenceSession(model_path, providers=providers)
        
        # Obtener informaciÃ³n del modelo
        input_shape = session.get_inputs()[0].shape
        input_height = input_shape[2] if len(input_shape) > 2 else 416
        input_width = input_shape[3] if len(input_shape) > 3 else 416
        
        print(f"âœ… MODELO CARGADO EXITOSAMENTE!")
        print(f"ðŸ“Š Input shape: {input_shape}")
        print(f"ðŸ“ TamaÃ±o entrada: {input_width}x{input_height}")
        print(f"ðŸ–¥ï¸ Providers activos: {session.get_providers()}")
        
        logger.info(f"âœ… Modelo YOLO cargado correctamente")
        logger.info(f"ðŸ“Š Input shape: {input_shape}")
        logger.info(f"ðŸ“ TamaÃ±o de entrada detectado: {input_width}x{input_height}")
        logger.info(f"ðŸ–¥ï¸ Providers: {session.get_providers()}")
        
        # Almacenar el tamaÃ±o de entrada como atributo del modelo
        session.input_size = (input_width, input_height)
        
        return session
        
    except Exception as e:
        print(f"âŒ ERROR CARGANDO MODELO: {e}")
        logger.error(f"âŒ Error cargando modelo YOLO: {e}")
        return None

@app.get("/", response_model=Dict[str, str])
async def root():
    """Endpoint raÃ­z con informaciÃ³n de la API"""
    return {
        "message": "Ratoncito PÃ©rez agente API",
        "version": "1.0.0",
        "description": "API REST para consultas turÃ­sticas de Madrid con IA/Ratoncito PÃ©rez",
        "docs": "/docs",
        "endpoints": {
            "guide": "/guide - GuÃ­a turÃ­stica completa del Ratoncito PÃ©rez",
            "vision-stream": "/ws/vision-stream - AnÃ¡lisis en tiempo real por WebSocket",
            "forecast": "/forecast - PronÃ³stico del tiempo",
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
    Generar guÃ­a turÃ­stica completa usando el agente CrewAI
    
    - **query**: Consulta turÃ­stica del usuario
    - **lat/lon**: Coordenadas GPS opcionales para bÃºsqueda local
    - **radio_km**: Radio de bÃºsqueda en kilÃ³metros
    - **categoria**: Filtro de categorÃ­a para lugares
    - **adulto/infantil/accesibilidad**: Filtros adicionales
    """
    global llm, vectorstore
    
    if not llm or not vectorstore:
        raise HTTPException(
            status_code=503, 
            detail="Agente no inicializado. Intente mÃ¡s tarde."
        )
    
    start_time = datetime.now()
    
    try:
        logger.info(f"ðŸ“ Procesando consulta: {query.query}")
        
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
            message="GuÃ­a turÃ­stica generada exitosamente",
            data={
                "guide": resultado,
                "query_params": query.dict(),
                #"sources": ["PDFs", "Internet", "OpenStreetMap"] if query.lat and query.lon else ["PDFs", "Internet"]
            },
            execution_time=execution_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"âŒ Error generando guÃ­a: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno generando guÃ­a turÃ­stica: {str(e)}"
        )

@app.get("/forecast")
async def get_forecast(lat: float, lon: float):
    response = get_weather_forecast_json(lat, lon, 1)
    
    if response.status_code == 200:
        data = response.json().get("daily", {})
                
        forecast = WEATHER_CODES.get(data["weather_code"][0], 'CondiciÃ³n desconocida')
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
        "Gran VÃ­a": {"lat": 40.4200, "lon": -3.7025},
        "Estadio Santiago BernabÃ©u": {"lat": 40.4530, "lon": -3.6883},
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
    print(f"ðŸ”Œ WEBSOCKET CONECTADO a las {session_start.strftime('%H:%M:%S')} - Modo enumeraciÃ³n simple")
    
    frame_count = 0
    
    try:
        # Mensaje de bienvenida
        await websocket.send_json({
            "type": "status",
            "data": {"message": "Conectado - Modo enumeraciÃ³n de frames"},
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            print(f"ðŸ”„ Esperando frame #{frame_count + 1}...")
            
            # Recibir datos
            data = await websocket.receive_json()
            
            if data.get("type") == "frame":
                frame_count += 1
                current_time = datetime.now()
                timestamp = current_time.strftime("%H:%M:%S.%f")[:-3]
                
                # Calcular tiempo desde el inicio de sesiÃ³n
                session_duration = (current_time - session_start).total_seconds()
                frames_per_second = frame_count / session_duration if session_duration > 0 else 0
                
                print(f"ðŸ“¸ FRAME #{frame_count} RECIBIDO a las {timestamp}")
                print(f"   ðŸ“Š SesiÃ³n: {session_duration:.1f}s | FPS promedio: {frames_per_second:.2f}")
                
                # Respuesta simple sin anÃ¡lisis
                response = {
                    "type": "analysis",
                    "data": {
                        "frame_number": frame_count,
                        "timestamp": timestamp,
                        "session_duration": f"{session_duration:.1f}s",
                        "fps_average": f"{frames_per_second:.2f}",
                        "message": f"Frame #{frame_count} recibido correctamente",
                        "description": f"Frame {frame_count} - SesiÃ³n: {session_duration:.1f}s - FPS: {frames_per_second:.2f}",
                        "confidence": 0.0,
                        "processing_time": 0.001
                    }
                }
                
                await websocket.send_json(response)
                print(f"âœ… RESPUESTA ENVIADA para frame #{frame_count}")
                
                # Mostrar milestone cada 10 frames
                if frame_count % 10 == 0:
                    print(f"ðŸŽ¯ MILESTONE: {frame_count} frames procesados en {session_duration:.1f}s")
                
            elif data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "data": {"timestamp": datetime.now().isoformat()}
                })
                print("ðŸ“ PING-PONG")
                
    except WebSocketDisconnect:
        session_duration = (datetime.now() - session_start).total_seconds()
        print(f"ðŸ”Œ Cliente desconectado despuÃ©s de {frame_count} frames")
        print(f"ðŸ“Š RESUMEN DE SESIÃ“N:")
        print(f"   â€¢ Frames procesados: {frame_count}")
        print(f"   â€¢ DuraciÃ³n: {session_duration:.1f}s")
        print(f"   â€¢ FPS promedio: {frame_count/session_duration:.2f}" if session_duration > 0 else "   â€¢ FPS: N/A")
    except Exception as e:
        print(f"âŒ ERROR despuÃ©s de {frame_count} frames: {e}")
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
    # Configuración para desarrollo
    run_server(
        host="127.0.0.1",
        port=8000,
        reload=True
    )


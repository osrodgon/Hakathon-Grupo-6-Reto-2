"""
FastAPI Backend - Ratoncito Pérez API
Versión con YOLOv8 nativo usando Ultralytics
"""
import asyncio
import uvicorn
from pydantic import BaseModel, Field
import base64
import json
import time
import cv2
import numpy as np
import os
import sys
from io import BytesIO
from PIL import Image
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, List, Optional, Any

# Imports - Machine Learning 
import torch
import torch.nn.functional as F
from ultralytics import YOLO
from huggingface_hub import hf_hub_download
from agent.agente_coordenadas import WEATHER_CODES, get_weather_forecast_json

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# ============== CONFIGURACIÓN YOLO ==============
HF_TOKEN = os.getenv('HF_TOKEN')  # Token para descargar modelos

# Configuración del modelo YOLO personalizado
YOLO_REPO_ID = "juancmamacias/hakathon_f5_mil"
YOLO_FILENAME = "best.pt"

# Solo detecta Ratoncito Pérez (clase 0)
RATONCITO_CLASS_ID = 0
RATONCITO_CLASS_NAME = "ratoncito_perez"

INPUT_SIZE = 416
CONF_THRESHOLD = 0.5
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, vectorstore, yolo_model
    """Gestión del ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando Ratoncito Pérez API...")
    
    # Cargar modelo YOLO al inicio
    global model
    model = await load_yolo_model()
    # Configurar LLM
    logger.info("âš™ï¸ Configurando LLM Gemini...")
    llm = crear_llm_gemini()
        
        # Inicializar vectorstore
    logger.info("ðŸ“š Inicializando vectorstore...")
    vectorstore = inicializar_vectorstore()
    logger.info("✅ Ratoncito Pérez API iniciado correctamente")
    yield
    # Cleanup al finalizar
    logger.info("🔌 Cerrando Ratoncito Pérez API...")

app = FastAPI(
    title="Ratoncito Pérez Madrid API",
    description="API para guía turística de Madrid con detección de personas",
    version="2.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
# ============== FUNCIONES YOLO ==============

async def load_yolo_model():
    """Cargar modelo YOLOv8 personalizado desde HuggingFace"""
    logger.info("🔥 Cargando modelo YOLOv8 personalizado desde HuggingFace...")
    
    try:
        # Descargar modelo desde HuggingFace
        logger.info(f"📥 Descargando modelo desde {YOLO_REPO_ID}")
        model_path = hf_hub_download(
            repo_id=YOLO_REPO_ID,
            filename=YOLO_FILENAME,
            token=HF_TOKEN
        )
        logger.info(f"✅ Modelo descargado en: {model_path}")
        
        # Cargar modelo YOLOv8 nativo
        model = YOLO(model_path)
        
        # Verificar CUDA
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"🎯 Dispositivo: {device}")
        
        # Mover modelo al dispositivo
        model.to(device)
        
        logger.info("✅ Modelo YOLOv8 cargado correctamente")
        logger.info(f"📋 Modelo: {YOLO_FILENAME}")
        logger.info(f"🎯 Clase objetivo: {RATONCITO_CLASS_ID} ({RATONCITO_CLASS_NAME})")
        
        return model
        
    except Exception as e:
        logger.error(f"❌ Error cargando modelo YOLO: {e}")
        raise e

def preprocess_frame(frame: np.ndarray) -> np.ndarray:
    """Preprocessar frame para YOLOv8 (ya no necesario, YOLO lo hace automáticamente)"""
    return frame

def postprocess_results(results, conf_threshold: float = CONF_THRESHOLD):
    """Procesar resultados de YOLOv8 nativo"""
    detections = []
    
    for result in results:
        # Obtener boxes, confianzas y clases
        if result.boxes is not None:
            boxes = result.boxes.xyxy.cpu().numpy()  # coordenadas x1,y1,x2,y2
            confidences = result.boxes.conf.cpu().numpy()
            classes = result.boxes.cls.cpu().numpy()
            
            for box, conf, cls in zip(boxes, confidences, classes):
                if conf >= conf_threshold and int(cls) == RATONCITO_CLASS_ID:
                    x1, y1, x2, y2 = box
                    detection = {
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'confidence': float(conf),
                        'class_id': int(cls),
                        'class_name': RATONCITO_CLASS_NAME
                    }
                    detections.append(detection)
    
    return detections

# ============== WEBSOCKET STREAMING ==============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint para streaming de cámara con detección YOLOv8"""
    await websocket.accept()
    logger.info("🔌 WEBSOCKET CONECTADO - Análisis con YOLOv8 nativo")
    
    global model
    if model is None:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Modelo YOLO no disponible"
        }))
        return
    
    frame_count = 0
    error_count = 0
    start_time = time.time()
    
    try:
        while True:
            # Recibir frame del cliente con timeout
            try:
                # Agregar timeout de 30 segundos para evitar bucle infinito
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Validar que los datos no estén vacíos o sean solo espacios
                if not data or data.strip() == "":
                    logger.warning("⚠️ Datos vacíos recibidos del WebSocket, ignorando...")
                    continue
                
                # Detectar si los datos son una imagen directa o JSON
                if data.strip().startswith('data:image/'):
                    # Cliente envía imagen directamente, crear JSON wrapper
                    logger.info("📸 Recibida imagen directa, convirtiendo a formato JSON...")
                    frame_data = {
                        "type": "frame",
                        "data": data.strip()
                    }
                elif data.strip().startswith('{'):
                    # Datos parecen JSON, intentar parsear
                    try:
                        frame_data = json.loads(data)
                        error_count = 0  # Reset counter en caso de éxito
                    except json.JSONDecodeError as e:
                        error_count += 1
                        if error_count <= 5:  # Solo mostrar primeros 5 errores
                            logger.error(f"❌ Error parsing JSON #{error_count}: {e}")
                            logger.error(f"📄 Primeros 200 caracteres: {repr(data[:200])}")
                            logger.error(f"📄 Últimos 50 caracteres: {repr(data[-50:])}")
                            logger.error(f"📏 Longitud total: {len(data)} caracteres")
                        elif error_count == 6:
                            logger.error("❌ Demasiados errores JSON, silenciando logs...")
                        continue
                    except Exception as e:
                        error_count += 1
                        if error_count <= 5:
                            logger.error(f"❌ Error inesperado procesando JSON #{error_count}: {e}")
                        continue
                else:
                    # Datos no reconocidos
                    logger.warning(f"⚠️ Formato de datos no reconocido: {data[:50]}...")
                    continue
                
            except asyncio.TimeoutError:
                logger.warning("⏰ Timeout esperando datos del cliente (30s)")
                # Enviar ping para verificar conexión
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                    logger.info("📡 Ping enviado al cliente")
                except:
                    logger.error("❌ Cliente desconectado (no se pudo enviar ping)")
                    break
                continue
            except WebSocketDisconnect:
                logger.info("🔌 Cliente desconectado normalmente")
                break
            except Exception as e:
                logger.error(f"❌ Error recibiendo datos WebSocket: {e}")
                break
            
            # Validar que frame_data es un diccionario válido
            if not isinstance(frame_data, dict):
                logger.error(f"❌ frame_data no es un diccionario: {type(frame_data)}")
                continue
            
            # Validar que tiene el campo 'type'
            if "type" not in frame_data:
                logger.error("❌ Campo 'type' no encontrado en frame_data")
                continue
            
            if frame_data.get("type") == "frame":
                frame_count += 1
                
                try:
                    # Validar que existe el campo data
                    if "data" not in frame_data:
                        logger.error("❌ Campo 'data' no encontrado en frame_data")
                        continue
                    
                    # Decodificar imagen con mejor manejo de formatos
                    image_data_str = frame_data["data"]
                    logger.info(f"📄 Procesando imagen: {len(image_data_str)} caracteres")
                    
                    try:
                        # Remover prefijo data:image si existe
                        if "," in image_data_str and image_data_str.startswith('data:image/'):
                            # Formato: data:image/jpeg;base64,XXXX
                            base64_data = image_data_str.split(",")[1]
                            logger.info("🔧 Removido prefijo data:image/")
                        else:
                            # Asumir que es base64 puro
                            base64_data = image_data_str
                        
                        # Decodificar base64
                        image_data = base64.b64decode(base64_data)
                        logger.info(f"✅ Base64 decodificado: {len(image_data)} bytes")
                        
                        # Convertir a imagen
                        image = Image.open(BytesIO(image_data)).convert("RGB")
                        frame = np.array(image)
                        logger.info(f"✅ Imagen procesada: {frame.shape}")
                        
                    except Exception as img_error:
                        logger.error(f"❌ Error específico procesando imagen: {img_error}")
                        logger.error(f"📄 Muestra de datos: {image_data_str[:100]}...")
                        continue
                    
                except Exception as e:
                    logger.error(f"❌ Error general procesando imagen en frame #{frame_count}: {e}")
                    continue
            
            elif frame_data.get("type") == "ping":
                # Responder al ping para mantener conexión viva
                await websocket.send_text(json.dumps({"type": "pong"}))
                logger.info("📡 Pong enviado en respuesta al ping del cliente")
                continue
            
            elif frame_data.get("type") == "close":
                # Cliente solicita cerrar conexión
                logger.info("🔌 Cliente solicita cerrar conexión")
                break
                
            else:
                logger.warning(f"⚠️ Tipo de mensaje desconocido: {frame_data.get('type')}")
                continue
            
            # Procesar frame (solo si llegamos aquí, es tipo "frame")
            # Guardar solo los primeros 10 frames
            #if frame_count <= 10:
            #    print("Guardando frame de prueba...")
            #    frame_filename = f"frame_{frame_count:03d}.jpg"
            #    cv2.imwrite(frame_filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            #    logger.info(f"💾 Frame #{frame_count} guardado como {frame_filename}")
            # Estadísticas del frame
            brightness = np.mean(frame)
            h, w = frame.shape[:2]
            logger.info(f"📸 Frame #{frame_count}: {w}x{h}, Brillo: {brightness:.1f}")
            
            # YOLOv8 - Predicción cada 30 frames
            detections = []
            
            if frame_count % 30 == 0:
                logger.info("🚀 ===== USANDO YOLOv8 NATIVO =====")
                logger.info("🎯 model.predict() - Iniciando predicción...")
            
            try:
                # ¡AQUÍ ESTÁ! La sintaxis que querías: model.predict()
                results = model.predict(
                    source=frame,
                    conf=CONF_THRESHOLD,
                    show=False,
                    save=False,
                    verbose=False
                )
                
                logger.info(f"   📋 Parámetros: conf={CONF_THRESHOLD}, show=False, save=False")
                
                # Procesar resultados
                detections = postprocess_results(results, CONF_THRESHOLD)
                
                logger.info("🎯 model.predict() ejecutado exitosamente!")
                logger.info(f"📊 Resultados: {len(detections)} Ratoncitos Pérez detectados")
                
                # Dibujar bounding boxes en la imagen si hay detecciones
                annotated_frame = frame.copy()
                if detections:
                    logger.info(f"✅ model.predict() detectó {len(detections)} Ratoncitos Pérez en frame #{frame_count}")
                    for i, det in enumerate(detections):
                        logger.info(f"  🐭 Ratoncito {i+1}: Confianza {det['confidence']:.3f}")
                        
                        # Dibujar bounding box
                        x1, y1, x2, y2 = map(int, det['bbox'])
                        
                        # Dibujar rectángulo
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        
                        # Dibujar etiqueta con confianza
                        label = f"Ratoncito Perez {det['confidence']:.2f}"
                        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                        
                        # Fondo para el texto
                        cv2.rectangle(annotated_frame, (x1, y1-25), (x1 + label_size[0], y1), (0, 255, 0), -1)
                        
                        # Texto
                        cv2.putText(annotated_frame, label, (x1, y1-5), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                else:
                    logger.info(f"❌ model.predict() no detectó Ratoncito Pérez en frame #{frame_count}")
                
                # Convertir imagen anotada a base64 para enviar al frontend
                annotated_image = Image.fromarray(annotated_frame)
                buffered = BytesIO()
                annotated_image.save(buffered, format="JPEG", quality=70)
                annotated_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                annotated_data_url = f"data:image/jpeg;base64,{annotated_base64}"

            except Exception as e:
                logger.error(f"❌ Error en model.predict(): {e}")

            
            # Estadísticas de FPS
            if frame_count % 10 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                logger.info(f"🎯 {frame_count} frames | {fps:.1f} FPS | {elapsed:.1f}s")
            
            # Enviar respuesta al cliente
            try:
                response = {
                    "type": "detection",
                    "frame_count": frame_count,
                    "detections": detections,
                    "fps": round(frame_count / (time.time() - start_time), 1) if frame_count > 0 else 0,
                    "annotated_image": annotated_data_url if 'annotated_data_url' in locals() else None,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send_text(json.dumps(response))
            
            except Exception as e:
                logger.error(f"❌ Error enviando respuesta WebSocket: {e}")
                break
                
    except WebSocketDisconnect:
        elapsed = time.time() - start_time
        logger.info(f"🔌 Cliente desconectado después de {frame_count} frames en {elapsed:.1f}s")
    except Exception as e:
        logger.error(f"❌ Error en WebSocket: {e}")
        await websocket.close()

# ============== ENDPOINTS REST ==============
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


@app.get("/")
async def root():
    """Endpoint de prueba"""
    return {
        "message": "Ratoncito Pérez Madrid API",
        "version": "2.0.0",
        "status": "active",
        "yolo_model": YOLO_FILENAME,
        "yolo_repo": YOLO_REPO_ID,
        "target_class": RATONCITO_CLASS_NAME,
        "device": "cuda" if torch.cuda.is_available() else "cpu"
    }

@app.get("/health")
async def health():
    """Endpoint de salud"""
    global model
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "cuda_available": torch.cuda.is_available(),
        "timestamp": datetime.now().isoformat()
    }

# ============== INICIAR SERVIDOR ==============
if __name__ == "__main__":
    uvicorn.run(
        "app_ultralytics:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

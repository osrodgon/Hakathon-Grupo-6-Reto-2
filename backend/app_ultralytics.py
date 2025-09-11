"""
FastAPI Backend - Ratoncito Pérez API
Versión con YOLOv8 nativo usando Ultralytics
"""
import asyncio
import uvicorn
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

INPUT_SIZE = 640
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
    start_time = time.time()
    
    try:
        while True:
            # Recibir frame del cliente
            try:
                data = await websocket.receive_text()
                
                # Validar que los datos no estén vacíos
                if not data or data.strip() == "":
                    logger.warning("⚠️ Datos vacíos recibidos del WebSocket")
                    continue
                
                # Intentar parsear JSON
                try:
                    frame_data = json.loads(data)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Error parsing JSON: {e}")
                    logger.error(f"📄 Datos recibidos: {data[:100]}...")
                    continue
                
            except Exception as e:
                logger.error(f"❌ Error recibiendo datos WebSocket: {e}")
                continue
            
            if frame_data.get("type") == "frame":
                frame_count += 1
                
                try:
                    # Validar que existe el campo data
                    if "data" not in frame_data:
                        logger.error("❌ Campo 'data' no encontrado en frame_data")
                        continue
                    
                    # Decodificar imagen
                    image_data_str = frame_data["data"]
                    if "," in image_data_str:
                        image_data = base64.b64decode(image_data_str.split(",")[1])
                    else:
                        image_data = base64.b64decode(image_data_str)
                    
                    image = Image.open(BytesIO(image_data)).convert("RGB")
                    frame = np.array(image)
                    
                except Exception as e:
                    logger.error(f"❌ Error procesando imagen en frame #{frame_count}: {e}")
                    continue
            
            elif frame_data.get("type") == "ping":
                # Responder al ping para mantener conexión viva
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue
                
            else:
                logger.warning(f"⚠️ Tipo de mensaje desconocido: {frame_data.get('type')}")
                continue
            
            # Procesar frame (solo si llegamos aquí, es tipo "frame")
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
                        
                        if detections:
                            logger.info(f"✅ model.predict() detectó {len(detections)} Ratoncitos Pérez en frame #{frame_count}")
                            for i, det in enumerate(detections):
                                logger.info(f"  � Ratoncito {i+1}: Confianza {det['confidence']:.3f}")
                        else:
                            logger.info(f"❌ model.predict() no detectó Ratoncito Pérez en frame #{frame_count}")
                            
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
                        "fps": round(frame_count / (time.time() - start_time), 1) if frame_count > 0 else 0
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

@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    """Endpoint para predicción en imagen estática"""
    global model
    
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo YOLO no disponible")
    
    try:
        # Leer imagen
        image_data = await file.read()
        image = Image.open(BytesIO(image_data)).convert("RGB")
        frame = np.array(image)
        
        # Predicción con YOLOv8
        results = model.predict(
            source=frame,
            conf=CONF_THRESHOLD,
            show=False,
            save=False,
            verbose=False
        )
        
        # Procesar resultados
        detections = postprocess_results(results, CONF_THRESHOLD)
        
        return {
            "detections": detections,
            "count": len(detections),
            "model": YOLO_FILENAME,
            "confidence_threshold": CONF_THRESHOLD
        }
        
    except Exception as e:
        logger.error(f"❌ Error en predicción: {e}")
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "app_ultralytics:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

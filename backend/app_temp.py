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

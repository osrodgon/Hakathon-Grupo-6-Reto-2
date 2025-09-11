#!/usr/bin/env python3
"""
FastAPI Application para el Agente Turístico de Madrid
Backend API REST para el agente CrewAI con Gemini + PDFs + OpenStreetMap
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import sys
import asyncio
from datetime import datetime
import logging
import os, glob, time
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession  # OJO: SQLModel, no SQLAlchemy

# Carga variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Importa el store adecuado según DB_PROVIDER - SQLite o MongoDB
from db.factory import get_store
store = get_store()

# === imports para la BD/servicios (añadir) ===
# SQLModel + SQLite
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from models.database import init_db, get_session
from services.seed_pois import seed_pois_if_needed
from services.location_service import save_location, prune_expired
from services.recommend_service import top_pois

logger = logging.getLogger("app")


# helpers para vectorstore de ubicaciones
def _vstore_dir():
    # Directorio de la caché FAISS (por defecto backend/vectorstore_cache)
    return os.getenv("LOCATION_VECTORSTORE_DIR") or os.path.join(os.path.dirname(__file__), "vectorstore_cache")

def _pdf_dir():
    # Directorio con los PDFs fuente (por defecto backend/pdfs_madrid)
    return os.getenv("LOCATION_PDF_DIR") or os.path.join(os.path.dirname(__file__), "pdfs_madrid")

def _ttl_days():
    # TTL (en días) leído de .env; si no se define → sin TTL
    raw = os.getenv("LOCATION_VECTORSTORE_TTL_DAYS")
    try:
        return int(raw) if raw not in (None, "") else None
    except ValueError:
        return None

def _cache_exists(d):
    # ¿Existen ambos archivos de FAISS?
    return os.path.exists(os.path.join(d, "index.faiss")) and os.path.exists(os.path.join(d, "index.pkl"))

def _cache_age_seconds(d):
    # Edad (segundos) de la caché (mínima de los dos archivos)
    f1, f2 = os.path.join(d, "index.faiss"), os.path.join(d, "index.pkl")
    return time.time() - min(os.path.getmtime(f1), os.path.getmtime(f2))

def _is_stale(d):
    # ¿Falta la caché o está caducada por TTL?
    if not _cache_exists(d):
        return True
    ttl = _ttl_days()
    if ttl is None:
        return False
    return _cache_age_seconds(d) > ttl * 86400

def _build_vectorstore_sync(logger):
    # Construye la caché FAISS a partir de los PDFs (bloqueante)
    d, pdir = _vstore_dir(), _pdf_dir()
    os.makedirs(d, exist_ok=True)
    pdfs = sorted(glob.glob(os.path.join(pdir, "*.pdf")))
    if not pdfs:
        logger.warning(f"[vectorstore] No hay PDFs en {pdir}; se omite construcción.")
        return
    docs = []
    for pdf in pdfs:
        docs.extend(PyPDFLoader(pdf).load())
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    emb = HuggingFaceEmbeddings(
        model_name=os.getenv("LOCATION_EMBEDDINGS_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    )
    vs = FAISS.from_documents(chunks, emb)
    vs.save_local(d)
    logger.info(f"[vectorstore] Guardado en {d}")



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

class LocationIn(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    age_range: Optional[str] = None       # "4-6" | "7-9" | "10-12"
    pmr: bool = False
    radius_m: int = 1000
    profile_type: Optional[str] = None    # "parent" | "child"

# Variables globales para el estado del agente
llm = None
vectorstore = None


# Reconstruye vectorstore ausente/obsoleto (TTL expired)
@app.on_event("startup")
async def _ensure_vectorstore():
    # Construcción SINCRÓNICA solo si falta o está caducado → evita el error del otro startup
    d = _vstore_dir()
    if _is_stale(d):
        logger.info("📚 Vectorstore ausente/obsoleto → reconstruyendo (bloqueante, primera vez)…")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _build_vectorstore_sync, logger)
    else:
        logger.info("📚 Vectorstore presente/fresco → OK")
    # ✅ marca listo
    app.state.vectorstore_ready = True
    
@app.on_event("startup")
async def startup_event():
    """Inicializar el agente al arrancar la aplicación"""
    global llm, vectorstore

    logger.info("🚀 Iniciando Ratoncito Pérez API...")

    try:
        # Configurar LLM + Vectorstore (para CrewAI)
        logger.info("⚙️ Configurando LLM Gemini...")
        llm = crear_llm_gemini()
        
        # Inicializar vectorstore
        logger.info("📚 Inicializando vectorstore...")
        vectorstore = inicializar_vectorstore()

        # === Inicialización de BD + semillas + limpieza TTL ===
        logger.info(f"🗄️ Inicializando almacenamiento (LOCAL={os.getenv('LOCAL','true')})...")
        await store.init()
        await store.seed_pois(pois=[])
        await store.prune_expired() # limpia ubicaciones expiradas
        
        logger.info("✅ Ratoncito Pérez API iniciado correctamente")

    except Exception as e:
        logger.error(f"❌ Error durante el startup: {e}")
        raise

# Endpoint raíz con info básica
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

# Endpoint CrewAI guide turístico
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
        "timestamp": datetime.now().isoformat()
    }


# Endpoint para verificar el estado del vectorstore o cache de ubicaciones
@app.get("/vectorstore/status", tags=["vectorstore"])
def vectorstore_status():
    d = _vstore_dir()
    exists = _cache_exists(d)
    ttl_raw = os.getenv("LOCATION_VECTORSTORE_TTL_DAYS")
    ttl = int(ttl_raw) if ttl_raw else None
    age = _cache_age_seconds(d) if exists else None
    stale = (ttl is not None and age is not None and age > ttl*86400)
    # Usa el flag; si no existiera por cualquier motivo, cae a un cálculo razonable
    ready = getattr(app.state, "vectorstore_ready", (exists and not stale))
    return {"dir": d, "exists": exists, "ttl_days": ttl, "age_seconds": age, "stale": stale, "ready": ready}


@app.get("/debug/db/summary")
async def db_summary():
    return await store.summary()

@app.get("/debug/db/pois")
async def db_pois():
    """Lista POIs de forma agnóstica usando top_pois con radio grande en Sol."""
    # Centro Madrid (Puerta del Sol) y radio grande para traer todos los seed
    out = await store.top_pois(lat=40.4169, lon=-3.7035, radius_m=50000, pmr=False, age_range=None, k=200)
    # Normaliza salida a id/name/lat/lon si está disponible
    # (top_pois devuelve id, name, distance_m, accessible, short)
    return out

from typing import List

@app.get("/debug/db/user/{user_id}/locations")
async def db_user_locations(user_id: str):
    import os
    is_local = (os.getenv("LOCAL", "true").lower() in ("1","true","yes","on"))

    if is_local:
        # --- SQLite (SQLModel) ---
        from sqlmodel import select
        from models.database import AsyncSessionLocal
        from models.entities import UserLocation
        async with AsyncSessionLocal() as s:
            rows = (await s.exec(
                select(UserLocation)
                .where(UserLocation.user_id == user_id)
                .order_by(UserLocation.created_at.desc())
            )).all()
        return [
            {
                "id": r.id,
                "lat": r.latitude,
                "lon": r.longitude,
                "created_at": r.created_at.isoformat(),
                "expires_at": r.expires_at.isoformat(),
            }
            for r in rows
        ]
    else:
        # --- Mongo Atlas (Motor) ---
        from motor.motor_asyncio import AsyncIOMotorClient
        MONGODB_URI = os.getenv("MONGODB_URI")
        MONGO_DB = os.getenv("MONGO_DB", "perez")
        if not MONGODB_URI:
            return {"error": "MONGODB_URI no definido"}

        # Reutiliza un cliente global sencillo para debug
        if not hasattr(app.state, "mongo_dbg_client"):
            app.state.mongo_dbg_client = AsyncIOMotorClient(MONGODB_URI)
        db = app.state.mongo_dbg_client[MONGO_DB]

        docs = await db.user_locations.find(
            {"user_id": user_id}
        ).sort("created_at", -1).to_list(200)

        return [
            {
                "id": str(d.get("_id")),
                "lat": d.get("latitude"),
                "lon": d.get("longitude"),
                "created_at": d.get("created_at").isoformat() if d.get("created_at") else None,
                "expires_at": d.get("expires_at").isoformat() if d.get("expires_at") else None,
            }
            for d in docs
        ]


# =====================   
# ===== FIN DEBUG =====


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


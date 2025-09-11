import os
import json
from pathlib import Path
from sqlmodel import select
from models.entities import POI
from models.database import AsyncSessionLocal

import logging
logger = logging.getLogger(__name__)

# --- RUTAS ROBUSTAS ---
# 1) Permite override por variable de entorno (útil en despliegues)
ENV_PATH = os.getenv("POIS_PATH")

# 2) Ruta canónica: backend/references/pois.json
BACKEND_DIR = Path(__file__).resolve().parents[1]      # .../backend
REF_CANON = BACKEND_DIR / "references" / "pois.json"

# 3) Fallback: por si alguien deja el viejo JSON junto al .py (no recomendado)
REF_FALLBACK = Path(__file__).with_name("seed_pois.json")

def _resolve_pois_path() -> Path | None:
    if ENV_PATH:
        p = Path(ENV_PATH)
        if p.exists():
            logger.info(f"[seed_pois] Cargando POIs desde POIS_PATH={p}")
            return p
        else:
            logger.warning(f"[seed_pois] POIS_PATH apunta a un archivo inexistente: {p}")
    if REF_CANON.exists():
        logger.info(f"[seed_pois] Cargando POIs desde {REF_CANON}")
        return REF_CANON
    if REF_FALLBACK.exists():
        logger.info(f"[seed_pois] Cargando POIs desde fallback {REF_FALLBACK}")
        return REF_FALLBACK
    logger.warning("[seed_pois] No se encontró archivo de POIs; se usará dataset mínimo por defecto.")
    return None

async def seed_pois_if_needed():
    async with AsyncSessionLocal() as s:
        existing = (await s.exec(select(POI))).all()
        if existing:
            return  # ya hay datos; no sembrar

        pois_path = _resolve_pois_path()

        # === COMPROBACIÓN Y CARGA DEL JSON ===
        data = None
        if pois_path:
            raw = pois_path.read_text(encoding="utf-8").strip()
            if not raw:
                logger.warning(f"[seed_pois] Archivo vacío: {pois_path}. Se usará dataset mínimo.")
            else:
                try:
                    data = json.loads(raw)
                    if not isinstance(data, list):
                        logger.warning(f"[seed_pois] El JSON no es una lista; se usará dataset mínimo. Tipo: {type(data)}")
                        data = None
                except Exception as e:
                    logger.warning(f"[seed_pois] JSON inválido en {pois_path}: {e}. Se usará dataset mínimo.")
        # === FIN COMPROBACIÓN ===

        # Fallback mínimo si no hay archivo o es inválido
        if not data:
            data = [
                {
                    "id": "poi_casa_perez",
                    "name": "Casa Museo del Ratón Pérez",
                    "lat": 40.4179,
                    "lon": -3.7065,
                    "kids_friendly": True,
                    "accessible": True,
                    "short": "Pequeño museo dedicado al famoso ratoncito."
                },
                {
                    "id": "poi_puerta_sol",
                    "name": "Puerta del Sol",
                    "lat": 40.4169,
                    "lon": -3.7035,
                    "kids_friendly": True,
                    "accessible": True,
                    "short": "La plaza más célebre de Madrid."
                }
            ]

        # Inserción
        inserted = 0
        for p in data:
            s.add(POI(
                id=p["id"],
                name=p["name"],
                latitude=p["lat"],
                longitude=p["lon"],
                kids_friendly=p.get("kids_friendly", True),
                accessible=p.get("accessible", True),
                short=p.get("short"),
                source=p.get("source")
            ))
            inserted += 1

        await s.commit()
        logger.info(f"[seed_pois] Insertados {inserted} POIs.")
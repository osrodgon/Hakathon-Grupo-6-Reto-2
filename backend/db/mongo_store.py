# backend/db/mongo_store.py
import os, json, logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse
from motor.motor_asyncio import AsyncIOMotorClient

from .interface import Storage

logger = logging.getLogger(__name__)

POIS_PATH = Path(os.getenv("POIS_PATH", "backend/references/pois.json"))
MONGODB_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGO_DB", "perez")

def _load_seed_pois() -> List[Dict]:
    if POIS_PATH.exists():
        raw = POIS_PATH.read_text(encoding="utf-8").strip()
        if raw:
            try:
                data = json.loads(raw)
                if isinstance(data, list):
                    return data
            except Exception as e:
                logger.warning(f"[MongoStore] JSON inválido en {POIS_PATH}: {e}")
    # fallback mínimo
    return [
        {"id":"poi_casa_perez","name":"Casa Museo del Ratón Pérez","lat":40.4179,"lon":-3.7065,"kids_friendly":True,"accessible":True,"short":"Pequeño museo dedicado al famoso ratoncito."},
        {"id":"poi_puerta_sol","name":"Puerta del Sol","lat":40.4169,"lon":-3.7035,"kids_friendly":True,"accessible":True,"short":"La plaza más célebre de Madrid."}
    ]

class MongoStore(Storage):
    def __init__(self):
        if not MONGODB_URI:
            raise RuntimeError("MONGODB_URI no definido")
        host = urlparse(MONGODB_URI).hostname
        logger.info(f"[MongoStore] Conectando a host={host} db={MONGO_DB}")
        # Server selection timeout corto para fallar rápido si hay problema
        self.client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        self.db = self.client[MONGO_DB]

    async def init(self) -> None:
        """
        Crea índices necesarios:
        - TTL en user_locations.expires_at
        - 2dsphere en pois.loc
        """
        # ¡Ojo! Si no existe la colección, create_index la crea
        await self.db.user_locations.create_index("expires_at", expireAfterSeconds=0)
        await self.db.pois.create_index([("loc", "2dsphere")])

    async def seed_pois(self, pois: List[Dict]) -> None:
        """Inserta POIs si la colección está vacía (upsert por id)."""
        cnt = await self.db.pois.estimated_document_count()
        if cnt > 0 and not pois:
            return

        if not pois:
            pois = _load_seed_pois()

        ops = []
        for p in pois:
            ops.append({
                "update_one": {
                    "filter": {"_id": p["id"]},
                    "update": {"$set": {
                        "name": p["name"],
                        # GeoJSON: lon,lat
                        "loc": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
                        "kids_friendly": p.get("kids_friendly", True),
                        "accessible": p.get("accessible", True),
                        "short": p.get("short")
                    }},
                    "upsert": True
                }
            })
        if ops:
            from pymongo import UpdateOne
            await self.db.pois.bulk_write([UpdateOne(**op["update_one"]) for op in ops])
        logger.info(f"[MongoStore] POIs listos (total ~{await self.db.pois.estimated_document_count()}).")

    async def save_location(self, user_id: str, lat: float, lon: float, ttl_days: int,
                            profile_type: Optional[str], has_mobility_issues: bool,
                            age_range: Optional[str]) -> None:
        await self.db.users.update_one(
            {"_id": user_id},
            {"$set": {
                "profile_type": profile_type,
                "has_mobility_issues": has_mobility_issues,
                "age_range": age_range,
                "updated_at": datetime.utcnow(),
            }},
            upsert=True
        )
        await self.db.user_locations.insert_one({
            "user_id": user_id,
            "latitude": lat,
            "longitude": lon,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=ttl_days or 3)
        })

    async def top_pois(self, lat: float, lon: float, radius_m: int = 1000,
                       pmr: bool = False, age_range: Optional[str] = None, k: int = 3) -> List[Dict]:
        """
        Devuelve POIs más cercanos (hasta 50) usando $geoNear (metros),
        y repuntúa con PMR/edad.
        """
        pipeline = [
            {"$geoNear": {
                "near": {"type": "Point", "coordinates": [lon, lat]},
                "distanceField": "distance_m",
                "maxDistance": radius_m,
                "spherical": True
            }},
            {"$limit": 50}
        ]
        docs = [d async for d in self.db.pois.aggregate(pipeline)]
        ranked = []
        for p in docs:
            pmr_fit = 1.0 if (not pmr or p.get("accessible")) else 0.3
            age_fit = 1.0 if (age_range is None or p.get("kids_friendly", True)) else 0.7
            base = 1 / (1 + p["distance_m"] / 300)
            ranked.append((0.5 * base + 0.3 * pmr_fit + 0.2 * age_fit, p))
        ranked.sort(key=lambda x: x[0], reverse=True)
        out = []
        for _, p in ranked[:k]:
            out.append({
                "id": p["_id"],
                "name": p["name"],
                "distance_m": int(p["distance_m"]),
                "accessible": p.get("accessible", True),
                "short": p.get("short"),
            })
        return out

    async def summary(self) -> Dict:
        poi = await self.db.pois.estimated_document_count()
        usr = await self.db.users.estimated_document_count()
        loc = await self.db.user_locations.estimated_document_count()
        return {"poi": poi, "users": usr, "user_locations": loc}

    async def prune_expired(self) -> None:
        """
        Mongo tiene TTL automático, pero puedes limpiar manualmente
        por si hay clock drift o índices recién creados.
        """
        await self.db.user_locations.delete_many({"expires_at": {"$lt": datetime.utcnow()}})

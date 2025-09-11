# backend/db/mongo_store.py
import os, json, logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

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
        {
            "id": "poi_casa_perez",
            "name": "Casa Museo del Ratón Pérez",
            "lat": 40.4179,
            "lon": -3.7065,
            "kids_friendly": True,
            "accessible": True,
            "short": "Pequeño museo dedicado al famoso ratoncito.",
        },
        {
            "id": "poi_puerta_sol",
            "name": "Puerta del Sol",
            "lat": 40.4169,
            "lon": -3.7035,
            "kids_friendly": True,
            "accessible": True,
            "short": "La plaza más célebre de Madrid.",
        },
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
        - Índices para usuarios y logs de chat
        """
        # Fail fast si la conexión no es válida
        await self.client.admin.command("ping")

        # Índices "core"
        await self.db.user_locations.create_index("expires_at", expireAfterSeconds=0)
        await self.db.pois.create_index([("loc", "2dsphere")])

        # Usuarios (por id)
        await self.db.users.create_index("id", unique=True)

        # Prompts opcionales (si los usas en otro endpoint)
        await self.db.prompts.create_index([("user_id", 1), ("created_at", -1)])

        # 📌 Logs de chat (prompt + respuesta del agente)
        await self.db.chat_logs.create_index([("user_id", 1), ("created_at", -1)])
        # (Opcional) TTL para limpieza automática de chats (3 días)
        # await self.db.chat_logs.create_index("created_at", expireAfterSeconds=259200)

    # -------------------
    # SEED POIs
    # -------------------
    async def seed_pois(self, pois: List[Dict]) -> None:
        """Inserta/actualiza POIs si la colección está vacía (upsert por id)."""
        cnt = await self.db.pois.estimated_document_count()
        if cnt > 0 and not pois:
            return

        if not pois:
            pois = _load_seed_pois()

        ops = []
        for p in pois:
            ops.append(
                UpdateOne(
                    {"_id": p["id"]},
                    {
                        "$set": {
                            "name": p["name"],
                            # GeoJSON: lon,lat
                            "loc": {
                                "type": "Point",
                                "coordinates": [p["lon"], p["lat"]],
                            },
                            "kids_friendly": p.get("kids_friendly", True),
                            "accessible": p.get("accessible", True),
                            "short": p.get("short"),
                        }
                    },
                    upsert=True,
                )
            )
        if ops:
            await self.db.pois.bulk_write(ops)
        logger.info(
            f"[MongoStore] POIs listos (total ~{await self.db.pois.estimated_document_count()})."
        )

    # -------------------
    # USERS & LOCATIONS
    # -------------------
    async def ensure_user(
        self,
        user_id: str,
        profile_type: Optional[str] = None,
        has_mobility_issues: Optional[bool] = None,
        age_range: Optional[str] = None,
    ) -> None:
        doc = {"id": user_id}
        if profile_type is not None:
            doc["profile_type"] = profile_type
        if has_mobility_issues is not None:
            doc["has_mobility_issues"] = bool(has_mobility_issues)
        if age_range is not None:
            doc["age_range"] = age_range
        await self.db.users.update_one(
            {"id": user_id}, {"$setOnInsert": doc, "$set": {"updated_at": datetime.utcnow()}}, upsert=True
        )

    async def save_location(
        self,
        user_id: str,
        lat: float,
        lon: float,
        ttl_days: int,
        profile_type: Optional[str],
        has_mobility_issues: bool,
        age_range: Optional[str],
    ) -> None:
        await self.ensure_user(
            user_id=user_id,
            profile_type=profile_type,
            has_mobility_issues=has_mobility_issues,
            age_range=age_range,
        )
        await self.db.user_locations.insert_one(
            {
                "user_id": user_id,
                "latitude": lat,
                "longitude": lon,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=ttl_days or 3),
            }
        )

    # -------------------
    # RECOMMENDATIONS
    # -------------------
    async def top_pois(
        self,
        lat: float,
        lon: float,
        radius_m: int = 1000,
        pmr: bool = False,
        age_range: Optional[str] = None,
        k: int = 3,
    ) -> List[Dict]:
        """
        Devuelve POIs más cercanos (hasta 50) usando $geoNear (metros),
        y repuntúa con PMR/edad.
        """
        pipeline = [
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [lon, lat]},
                    "distanceField": "distance_m",
                    "maxDistance": radius_m,
                    "spherical": True,
                }
            },
            {"$limit": 50},
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
            out.append(
                {
                    "id": p["_id"],
                    "name": p["name"],
                    "distance_m": int(p["distance_m"]),
                    "accessible": p.get("accessible", True),
                    "short": p.get("short"),
                }
            )
        return out

    # -------------------
    # CHAT LOGS (prompt + respuesta del agente)
    # -------------------
    async def save_chat_turn(
        self, user_id: str, prompt: str, response: str, model: Optional[str] = None
    ) -> str:
        doc = {
            "user_id": user_id,
            "prompt": prompt,
            "response": response,
            "model": model,
            "created_at": datetime.utcnow(),
        }
        res = await self.db.chat_logs.insert_one(doc)
        return str(res.inserted_id)

    async def get_chat_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        cur = (
            self.db.chat_logs.find({"user_id": user_id})
            .sort("created_at", -1)
            .limit(limit)
        )
        docs = await cur.to_list(length=limit)
        out: List[Dict] = []
        for d in docs:
            d["id"] = str(d.pop("_id"))
            if "created_at" in d and hasattr(d["created_at"], "isoformat"):
                d["created_at"] = d["created_at"].isoformat()
            out.append(d)
        return out

    async def get_chat_turn(self, turn_id: str) -> Optional[Dict]:
        try:
            oid = ObjectId(turn_id)
        except Exception:
            return None
        d = await self.db.chat_logs.find_one({"_id": oid})
        if not d:
            return None
        d["id"] = str(d.pop("_id"))
        if "created_at" in d and hasattr(d["created_at"], "isoformat"):
            d["created_at"] = d["created_at"].isoformat()
        return d

    # -------------------
    # SUMMARY & MAINTENANCE
    # -------------------
    async def summary(self) -> Dict:
        poi = await self.db.pois.estimated_document_count()
        usr = await self.db.users.estimated_document_count()
        loc = await self.db.user_locations.estimated_document_count()
        chats = await self.db.chat_logs.estimated_document_count()
        return {"poi": poi, "users": usr, "user_locations": loc, "chat_logs": chats}

    async def prune_expired(self) -> None:
        """
        Mongo tiene TTL automático, pero puedes limpiar manualmente
        por si hay clock drift o índices recién creados.
        """
        await self.db.user_locations.delete_many({"expires_at": {"$lt": datetime.utcnow()}})
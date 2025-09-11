# backend/db/sqlite_store.py
import os, json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from sqlmodel import select
from sqlalchemy import delete

from .interface import Storage
from services.recommend_service import haversine_m

# db.AsyncSessionLocal se actualiza tras init_db()
from models import database as db

from models.entities import POI, User, UserLocation, ChatTurn

POIS_PATH = Path(os.getenv("POIS_PATH", "backend/references/pois.json"))

class SQLiteStore(Storage):
    async def init(self) -> None:
        await db.init_db()

    async def seed_pois(self, pois: List[Dict]) -> None:
        if db.AsyncSessionLocal is None:
            await db.init_db()
        async with db.AsyncSessionLocal() as s:
            exists = (await s.exec(select(POI))).first()
            if exists:
                return

            # Carga del JSON si no pasan lista
            if not pois and POIS_PATH.exists():
                raw = POIS_PATH.read_text(encoding="utf-8").strip()
                if raw:
                    try:
                        pois = json.loads(raw)
                    except Exception:
                        pois = []

            # Fallback mínimo
            if not pois:
                pois = [
                    {"id":"poi_casa_perez","name":"Casa Museo del Ratón Pérez","lat":40.4179,"lon":-3.7065,"kids_friendly":True,"accessible":True,"short":"Pequeño museo dedicado al famoso ratoncito."},
                    {"id":"poi_puerta_sol","name":"Puerta del Sol","lat":40.4169,"lon":-3.7035,"kids_friendly":True,"accessible":True,"short":"La plaza más célebre de Madrid."}
                ]

            for p in pois:
                s.add(POI(
                    id=p["id"], name=p["name"],
                    latitude=p["lat"], longitude=p["lon"],
                    kids_friendly=p.get("kids_friendly", True),
                    accessible=p.get("accessible", True),
                    short=p.get("short")
                ))
            await s.commit()

    async def save_location(self, user_id: str, lat: float, lon: float, ttl_days: int,
                            profile_type: Optional[str], has_mobility_issues: bool,
                            age_range: Optional[str]) -> None:
        if db.AsyncSessionLocal is None:
            await db.init_db()
        async with db.AsyncSessionLocal() as s:
            user = await s.get(User, user_id)
            if not user:
                user = User(id=user_id, profile_type=profile_type,
                            has_mobility_issues=has_mobility_issues, age_range=age_range)
                s.add(user)
            else:
                if profile_type: user.profile_type = profile_type
                user.has_mobility_issues = has_mobility_issues
                if age_range: user.age_range = age_range

            exp = datetime.utcnow() + timedelta(days=ttl_days or 3)
            s.add(UserLocation(user_id=user_id, latitude=lat, longitude=lon, expires_at=exp))
            await s.commit()

    async def top_pois(self, lat: float, lon: float, radius_m: int = 1000,
                       pmr: bool = False, age_range: Optional[str] = None, k: int = 3) -> List[Dict]:
        if db.AsyncSessionLocal is None:
            await db.init_db()
        async with db.AsyncSessionLocal() as s:
            rows = (await s.exec(select(POI))).all()

        scored = []
        for p in rows:
            d = haversine_m((lat, lon), (p.latitude, p.longitude))
            if d > radius_m:
                continue
            pmr_fit = 1.0 if (not pmr or p.accessible) else 0.3
            age_fit = 1.0 if (age_range is None or p.kids_friendly) else 0.7
            dist_score = 1/(1 + d/300)
            scored.append((0.5*dist_score + 0.3*pmr_fit + 0.2*age_fit, int(d), p))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"id": p.id, "name": p.name, "distance_m": d, "accessible": p.accessible, "short": p.short}
            for _, d, p in scored[:k]
        ]

    async def summary(self) -> Dict:
        if db.AsyncSessionLocal is None:
            await db.init_db()
        async with db.AsyncSessionLocal() as s:
            pois = (await s.exec(select(POI))).all()
            users = (await s.exec(select(User))).all()
            locs = (await s.exec(select(UserLocation))).all()
        return {"poi": len(pois), "users": len(users), "user_locations": len(locs)}

    async def prune_expired(self) -> None:
        if db.AsyncSessionLocal is None:
            await db.init_db()
        async with db.AsyncSessionLocal() as s:
            await s.exec(
                delete(UserLocation).where(UserLocation.expires_at < datetime.utcnow())
            )
            await s.commit()

    async def ensure_user(self, user_id: str,
                          profile_type=None, has_mobility_issues=None, age_range=None) -> None:
        if db.AsyncSessionLocal is None:
            await db.init_db()
        async with db.AsyncSessionLocal() as s:
            u = await s.get(User, user_id)
            if not u:
                u = User(id=user_id,
                         profile_type=profile_type,
                         has_mobility_issues=bool(has_mobility_issues or False),
                         age_range=age_range)
                s.add(u)
            else:
                if profile_type: u.profile_type = profile_type
                if has_mobility_issues is not None: u.has_mobility_issues = has_mobility_issues
                if age_range: u.age_range = age_range
            await s.commit()

    async def save_chat_turn(self, user_id: str, prompt: str, response: str, model: str | None = None) -> str:
        if db.AsyncSessionLocal is None:
            await db.init_db()
        async with db.AsyncSessionLocal() as s:
            row = ChatTurn(user_id=user_id, prompt=prompt, response=response, model=model)
            s.add(row)
            await s.commit()
            await s.refresh(row)
            return str(row.id)

    async def get_chat_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        if db.AsyncSessionLocal is None:
            await db.init_db()
        async with db.AsyncSessionLocal() as s:
            q = await s.exec(
                select(ChatTurn)
                .where(ChatTurn.user_id == user_id)
                .order_by(ChatTurn.created_at.desc())
                .limit(limit)
            )
            rows = q.all()
        return [{
            "id": str(r.id), "user_id": r.user_id,
            "prompt": r.prompt, "response": r.response,
            "model": r.model, "created_at": r.created_at.isoformat()
        } for r in rows]

    async def get_chat_turn(self, turn_id: str) -> Optional[Dict]:
        if db.AsyncSessionLocal is None:
            await db.init_db()
        async with db.AsyncSessionLocal() as s:
            row = await s.get(ChatTurn, int(turn_id))
            if not row: return None
            return {
                "id": str(row.id), "user_id": row.user_id,
                "prompt": row.prompt, "response": row.response,
                "model": row.model, "created_at": row.created_at.isoformat()
            }
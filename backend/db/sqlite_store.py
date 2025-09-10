# backend/storage/sqlite_store.py
from .interface import Storage
from backend.models.database import AsyncSessionLocal
from backend.models.entities import POI, User, UserLocation
from backend.services.recommend_service import haversine_m
from datetime import datetime, timedelta
from sqlmodel import select
from sqlalchemy import text

class SQLiteStore(Storage):
    async def seed_pois(self, pois): ...  # insert si vacío (igual que ahora)
    async def save_location(self, user_id, lat, lon, ttl_days, profile_type, has_mobility_issues, age_range):
        async with AsyncSessionLocal() as s:
            user = await s.get(User, user_id) or User(id=user_id)
            user.profile_type = profile_type or user.profile_type
            user.has_mobility_issues = has_mobility_issues
            user.age_range = age_range or user.age_range
            s.add(user)
            s.add(UserLocation(user_id=user_id, latitude=lat, longitude=lon,
                               expires_at=datetime.utcnow()+timedelta(days=ttl_days)))
            await s.commit()
    async def top_pois(self, lat, lon, radius_m=1000, pmr=False, age_range=None, k=3):
        async with AsyncSessionLocal() as s:
            rows = (await s.exec(select(POI))).all()
        scored=[]
        for p in rows:
            d = haversine_m((lat,lon),(p.latitude,p.longitude))
            if d>radius_m: continue
            pmr_fit = 1.0 if (not pmr or p.accessible) else 0.3
            age_fit = 1.0 if (age_range is None or p.kids_friendly) else 0.7
            dist_score = 1/(1+d/300)
            scored.append((0.5*dist_score+0.3*pmr_fit+0.2*age_fit, int(d), p))
        scored.sort(key=lambda x:x[0], reverse=True)
        return [{"id":p.id,"name":p.name,"distance_m":d,"accessible":p.accessible,"short":p.short} for _,d,p in scored[:k]]

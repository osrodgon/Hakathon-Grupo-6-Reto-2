from datetime import datetime, timedelta
from sqlmodel import select
from sqlalchemy import text
from models.entities import User, UserLocation
from models.database import AsyncSessionLocal

async def save_location(user_id: str, lat: float, lon: float, ttl_days: int = 3,
                        profile_type=None, has_mobility_issues=False, age_range=None):
    async with AsyncSessionLocal() as s:
        # upsert user mínimo
        user = await s.get(User, user_id)
        if not user:
            user = User(id=user_id, profile_type=profile_type,
                        has_mobility_issues=has_mobility_issues, age_range=age_range)
            s.add(user)
        else:
            if age_range: user.age_range = age_range
            user.has_mobility_issues = has_mobility_issues

        exp = datetime.utcnow() + timedelta(days=ttl_days)
        s.add(UserLocation(user_id=user_id, latitude=lat, longitude=lon, expires_at=exp))
        await s.commit()

async def prune_expired():
    async with AsyncSessionLocal() as s:
        await s.exec(text("DELETE FROM userlocation WHERE expires_at < CURRENT_TIMESTAMP"))
        await s.commit()

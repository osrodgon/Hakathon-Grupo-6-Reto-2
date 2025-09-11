from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from backend.models.database import init_db, get_session
from backend.services.seed_pois import seed_pois_if_needed
from backend.services.location_service import save_location, prune_expired
from backend.services.recommend_service import top_pois
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI(title="Perez API")

@app.on_event("startup")
async def on_start():
    await init_db()
    await seed_pois_if_needed()
    await prune_expired()

class LocationIn(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    age_range: Optional[str] = None
    pmr: bool = False
    radius_m: int = 1000
    profile_type: Optional[str] = None

@app.post("/users/location")
async def users_location(loc: LocationIn):
    await save_location(loc.user_id, loc.latitude, loc.longitude, ttl_days=3,
                        profile_type=loc.profile_type, has_mobility_issues=loc.pmr, age_range=loc.age_range)
    return {"ok": True}

@app.post("/recommendations")
async def recommendations(loc: LocationIn, session: AsyncSession = Depends(get_session)):
    pois = await top_pois(session, loc.latitude, loc.longitude, loc.radius_m, loc.pmr, loc.age_range, k=3)
    return {"top": pois}


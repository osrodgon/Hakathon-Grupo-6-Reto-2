from math import radians, sin, cos, asin, sqrt
from typing import List, Dict, Any
from sqlmodel import select
from models.entities import POI

def haversine_m(a, b):
    lat1, lon1 = a; lat2, lon2 = b
    φ1, λ1, φ2, λ2 = map(radians, [lat1, lon1, lat2, lon2])
    dφ, dλ = φ2-φ1, λ2-λ1
    return 2*6371000*asin((sin(dφ/2)**2 + cos(φ1)*cos(φ2)*sin(dλ/2)**2) ** 0.5)

async def top_pois(session, lat: float, lon: float, radius_m=1000, pmr=False, age_range=None, k=3):
    rows = (await session.exec(select(POI))).all()
    scored=[]
    for p in rows:
        d = haversine_m((lat,lon),(p.latitude,p.longitude))
        if d > radius_m: continue
        pmr_fit = 1.0 if (not pmr or p.accessible) else 0.3
        age_fit = 1.0 if (age_range is None or p.kids_friendly) else 0.7
        dist_score = 1/(1+d/300)
        score = 0.5*dist_score + 0.3*pmr_fit + 0.2*age_fit
        scored.append((score, int(d), p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"id":p.id,"name":p.name,"distance_m":d,"accessible":p.accessible,"short":p.short} for _, d, p in scored[:k]]

# backend/storage/mongo_store.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from .interface import Storage
from datetime import datetime, timedelta

class MongoStore(Storage):
    def __init__(self):
        self.client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        self.db = self.client["perez"]
    async def seed_pois(self, pois):
        await self.db.pois.create_index([("loc","2dsphere")])
        await self.db.user_locations.create_index("expires_at", expireAfterSeconds=0)
        for p in pois:
            await self.db.pois.update_one(
              {"_id": p["id"]},
              {"$set": {"name":p["name"], "loc":{"type":"Point","coordinates":[p["lon"],p["lat"]]},
                        "kids_friendly":p.get("kids_friendly",True), "accessible":p.get("accessible",True),
                        "short":p.get("short")}},
              upsert=True
            )
    async def save_location(self, user_id, lat, lon, ttl_days, profile_type, has_mobility_issues, age_range):
        await self.db.users.update_one({"_id": user_id},
            {"$set":{"profile_type":profile_type,"has_mobility_issues":has_mobility_issues,
                     "age_range":age_range,"updated_at":datetime.utcnow()}}, upsert=True)
        await self.db.user_locations.insert_one({
            "user_id": user_id, "latitude": lat, "longitude": lon,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow()+timedelta(days=ttl_days)
        })
    async def top_pois(self, lat, lon, radius_m=1000, pmr=False, age_range=None, k=3):
        # $geoNear para distancia en metros:
        pipeline = [{
          "$geoNear":{
            "near":{"type":"Point","coordinates":[lon, lat]},
            "distanceField":"distance_m",
            "maxDistance": radius_m,
            "spherical": True
          }},
          {"$limit": 50}
        ]
        docs = [d async for d in self.db.pois.aggregate(pipeline)]
        ranked=[]
        for p in docs:
            pmr_fit = 1.0 if (not pmr or p.get("accessible")) else 0.3
            age_fit = 1.0 if (age_range is None or p.get("kids_friendly", True)) else 0.7
            base = 1/(1+p["distance_m"]/300)
            ranked.append((0.5*base+0.3*pmr_fit+0.2*age_fit, p))
        ranked.sort(key=lambda x:x[0], reverse=True)
        out=[]
        for _, p in ranked[:k]:
            out.append({"id": p["_id"], "name": p["name"],
                        "distance_m": int(p["distance_m"]),
                        "accessible": p.get("accessible"), "short": p.get("short")})
        return out

import asyncio
import sys
from pathlib import Path

# --- asegurar que podemos importar "backend" aunque ejecutes desde / ---
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlmodel import select
from backend.models.database import init_db, get_session
from backend.models.entities import POI, User, UserLocation

async def main():
    # crea tablas si no existen
    await init_db()

    # abre una sesión y consulta conteos + una muestra
    async for session in get_session():
        poi_rows = (await session.exec(select(POI))).all()
        user_rows = (await session.exec(select(User))).all()
        loc_rows = (await session.exec(select(UserLocation))).all()

        print("POIs:", len(poi_rows))
        print("Users:", len(user_rows))
        print("Locations:", len(loc_rows))

        # muestra los 3 primeros POIs
        for p in poi_rows[:3]:
            print(f"- {p.id} | {p.name} ({p.latitude}, {p.longitude})")
        break

if __name__ == "__main__":
    asyncio.run(main())

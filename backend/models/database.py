import os
from pathlib import Path
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession   
from sqlalchemy.orm import sessionmaker

# Directorios base
BACKEND_DIR = Path(__file__).resolve().parents[1]  # .../backend
ROOT_DIR = BACKEND_DIR.parent

DB_PROVIDER = os.getenv("DB_PROVIDER", "sqlite").lower()
RAW_DATABASE_URL = os.getenv("DATABASE_URL")   # opcional (p.ej. Postgres)
RAW_SQLITE_URL  = os.getenv("SQLITE_URL")      # p.ej. sqlite+aiosqlite:///backend/storage/perez.db

def _resolve_sqlite_url(raw: str | None) -> str:
    # default a backend/storage/perez.db
    if not raw:
        db_path = BACKEND_DIR / "storage" / "perez.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{db_path.as_posix()}"

    # Esperamos formato sqlite+aiosqlite:///RUTA
    if ":///" not in raw:
        # si alguien puso "sqlite+perez.db" mal formado, cae al default
        db_path = BACKEND_DIR / "storage" / "perez.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{db_path.as_posix()}"

    scheme, path = raw.split(":///", 1)
    if not scheme.startswith("sqlite"):
        # no es sqlite: dejar tal cual (por si alguien mete otra cosa por error)
        return raw

    p = Path(path)
    if not p.is_absolute():
        # Si te pasan "backend/storage/xxx.db" o "perez.db", lo anclamos al ROOT
        # para que "backend/..." funcione desde la raíz del repo.
        base = ROOT_DIR if path.startswith("backend") else BACKEND_DIR
        p = (base / path).resolve()

    p.parent.mkdir(parents=True, exist_ok=True)
    return f"{scheme}:///{p.as_posix()}"

# Construye la URL final
if RAW_DATABASE_URL:
    DATABASE_URL = RAW_DATABASE_URL
elif DB_PROVIDER == "sqlite":
    DATABASE_URL = _resolve_sqlite_url(RAW_SQLITE_URL)
else:
    raise RuntimeError("DB_PROVIDER no soportado por SQLAlchemy en esta build")

# (Opcional) Log de depuración para ver la ruta real
print(f"[DB] DATABASE_URL = {DATABASE_URL}")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
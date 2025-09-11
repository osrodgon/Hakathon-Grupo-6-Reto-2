# backend/models/database.py
import os
from pathlib import Path
from typing import Optional

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

# Directorios base
BACKEND_DIR = Path(__file__).resolve().parents[1]  # .../backend
ROOT_DIR = BACKEND_DIR.parent

# Estado global (no se inicializa en import)
engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[sessionmaker] = None
DATABASE_URL: Optional[str] = None


def _truthy(val: Optional[str]) -> bool:
    return (val or "").lower() in ("1", "true", "yes", "on")


def _is_sqlite_mode() -> bool:
    """
    Decide si estás en modo SQLite:
    - LOCAL=true → SQLite (prioritario para tu toggle actual)
    - o DB_PROVIDER=sqlite
    """
    if _truthy(os.getenv("LOCAL", "true")):
        return True
    return os.getenv("DB_PROVIDER", "sqlite").lower() == "sqlite"


def _resolve_sqlite_url(raw: Optional[str]) -> str:
    """
    Devuelve una URL sqlite+aiosqlite:/// absoluta y crea la carpeta si no existe.
    Soporta:
      - None → backend/storage/perez.db
      - 'algo.db' o 'backend/storage/loquesea.db'
      - 'sqlite+aiosqlite:///RUTA'
    """
    if not raw:
        db_path = BACKEND_DIR / "storage" / "perez.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{db_path.as_posix()}"

    if ":///" not in raw:
        # dieron un nombre relativo
        p = Path(raw)
        if not p.suffix:
            p = p.with_suffix(".db")
        if not p.is_absolute():
            base = ROOT_DIR if str(p).startswith("backend") else BACKEND_DIR
            p = (base / p).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{p.as_posix()}"

    # formato con esquema
    scheme, path = raw.split(":///", 1)
    if not scheme.startswith("sqlite"):
        raise ValueError("SQLITE_URL debe comenzar por sqlite+aiosqlite:///")
    p = Path(path)
    if not p.is_absolute():
        base = ROOT_DIR if path.startswith("backend") else BACKEND_DIR
        p = (base / path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return f"{scheme}:///{p.as_posix()}"


async def init_db() -> None:
    """
    Inicializa SQLite SOLO si estás en modo SQLite y aún no hay engine.
    En modo Mongo, no hace nada.
    """
    global engine, AsyncSessionLocal, DATABASE_URL

    if not _is_sqlite_mode():
        # Modo Mongo → no toques SQLite
        return

    if engine is not None:
        # Ya inicializado
        return

    raw_url = os.getenv("SQLITE_URL")  # p.ej. sqlite+aiosqlite:///backend/storage/perez.db
    DATABASE_URL = _resolve_sqlite_url(raw_url)

    # crea engine y sessionmaker (sin side effects en import)
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # importa los modelos aquí para registrar las tablas
    from models import entities as _entities  

    # crea tablas
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    """
    Devuelve una sesión async. Debes haber llamado ANTES a init_db().
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Base de datos SQLite no inicializada. Llama a init_db() primero.")
    async with AsyncSessionLocal() as session:
        yield session

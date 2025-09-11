import os
#from .sqlite_store import SQLiteStore
#from .mongo_store import MongoStore
from .interface import Storage

def _truthy(val: str | None) -> bool:
    return (val or "").lower() in ("1","true","yes","on")

def get_store() -> Storage:
    # Regla: LOCAL=true => SQLite ; si no, mira STORAGE_BACKEND
    local = _truthy(os.getenv("LOCAL", "true"))
    backend = (os.getenv("STORAGE_BACKEND", "sqlite") or "sqlite").lower()

    if local or backend == "sqlite":
        # importación perezosa
        from .sqlite_store import SQLiteStore
        return SQLiteStore()

    if backend == "mongo":
        from .mongo_store import MongoStore
        return MongoStore()

    # por defecto, SQLite
    from .sqlite_store import SQLiteStore
    return SQLiteStore()
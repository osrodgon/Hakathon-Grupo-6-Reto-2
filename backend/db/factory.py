# backend/storage/factory.py
import os
from .sqlite_store import SQLiteStore
from .mongo_store import MongoStore

def get_store():
    return MongoStore() if os.getenv("STORAGE_BACKEND")=="mongo" else SQLiteStore()

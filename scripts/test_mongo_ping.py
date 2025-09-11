# scripts/test_mongo_ping.py
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

URI ="mongodb+srv://rperez:35HpKbax9cUjyk@cluster-perez.qa1xey3.mongodb.net/?retryWrites=true&w=majority&appName=cluster-perez"
client = MongoClient(URI, server_api=ServerApi('1'), serverSelectionTimeoutMS=5000)

try:
    client.admin.command("ping")
    print("✅ Ping OK. Conectado a MongoDB Atlas.")
except Exception as e:
    print("❌ Error:", e)

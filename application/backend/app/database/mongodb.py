import os
import json
from typing import Optional, Any, Dict, List

# Check if motor/pymongo is available, with graceful fallback to JSON datasets
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo import MongoClient
    HAS_MONGODB_DRIVER = True
except ImportError:
    HAS_MONGODB_DRIVER = False

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB_NAME", "curaassist_db")

_async_client: Optional[Any] = None
_sync_client: Optional[Any] = None


def get_async_mongodb_client():
    global _async_client
    if not HAS_MONGODB_DRIVER:
        return None
    if _async_client is None:
        try:
            _async_client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=2500)
        except Exception as e:
            print("[MongoDB] Failed to initialize AsyncIOMotorClient:", e)
            _async_client = None
    return _async_client


def get_sync_mongodb_client():
    global _sync_client
    if not HAS_MONGODB_DRIVER:
        return None
    if _sync_client is None:
        try:
            _sync_client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=2500)
        except Exception as e:
            print("[MongoDB] Failed to initialize MongoClient:", e)
            _sync_client = None
    return _sync_client


def get_database(db_name: str = DB_NAME):
    client = get_sync_mongodb_client()
    if client:
        try:
            return client[db_name]
        except Exception as e:
            print(f"[MongoDB] Error accessing database {db_name}:", e)
    return None


def get_collection(collection_name: str):
    db = get_database()
    if db is not None:
        return db[collection_name]
    return None


def check_mongodb_connection() -> Dict[str, Any]:
    if not HAS_MONGODB_DRIVER:
        return {
            "status": "offline",
            "driverInstalled": False,
            "message": "PyMongo/Motor driver not installed. Falling back to local JSON datasets."
        }

    client = get_sync_mongodb_client()
    if not client:
        return {
            "status": "offline",
            "driverInstalled": True,
            "message": "MongoDB client initialization failed. Falling back to local JSON datasets."
        }

    try:
        # Ping database server
        client.admin.command('ping')
        return {
            "status": "online",
            "driverInstalled": True,
            "mongoUri": MONGODB_URL.split("@")[-1],
            "database": DB_NAME,
            "collections": client[DB_NAME].list_collection_names()
        }
    except Exception as e:
        return {
            "status": "standalone_fallback",
            "driverInstalled": True,
            "message": f"MongoDB server offline at {MONGODB_URL}. Using disk JSON datasets.",
            "error": str(e)
        }


def seed_initial_datasets_to_mongodb():
    """Seed initial JSON data files into MongoDB collections if empty"""
    db = get_database()
    if db is None:
        return {"status": "skipped", "reason": "MongoDB server offline or unreachable"}

    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    seeded = {}

    datasets = {
        "medicines": "medicines.json",
        "symptoms": "symptoms.json",
        "diseases": "diseases.json",
        "first_aid": "first_aid.json",
        "health_records": "health_records.json"
    }

    for coll_name, filename in datasets.items():
        try:
            coll = db[coll_name]
            if coll.count_documents({}) == 0:
                file_path = os.path.join(data_dir, filename)
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        records = json.load(f)
                        if isinstance(records, list) and len(records) > 0:
                            coll.insert_many(records)
                            seeded[coll_name] = len(records)
        except Exception as err:
            print(f"[MongoDB Seed Error] {coll_name}:", err)

    return {
        "status": "success",
        "seededCollections": seeded
    }

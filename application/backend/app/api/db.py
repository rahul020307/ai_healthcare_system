import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Body

from app.database.mongodb import check_mongodb_connection, get_database as get_mongo_db, seed_initial_datasets_to_mongodb
from app.database.postgresql import check_postgresql_connection

router = APIRouter(prefix="/db", tags=["Database Services"])

DATA_DIR = Path(__file__).parent.parent.parent / "data"

DATASET_FILES = {
    "medicines": "medicines.json",
    "health_records": "health_records.json",
    "hospitals": "hospitals.json",
    "doctors": "doctors.json",
    "pharmacies": "pharmacies.json",
    "bloodbanks": "bloodbanks.json",
    "clinics": "clinics.json",
    "laboratories": "laboratories.json",
    "ambulance_services": "ambulance_services.json",
    "symptoms": "symptoms.json",
    "diseases": "diseases.json",
    "first_aid": "first_aid.json",
    "drug_interactions": "drug_interactions.json",
    "generic_alternatives": "generic_alternatives.json",
    "medicine_categories": "medicine_categories.json",
    "medicine_barcodes": "medicine_barcodes.json",
    "medicine_images": "medicine_images.json",
    "faq": "faq.json",
    "health_tips": "health_tips.json",
    "offers": "offers.json",
    "reviews": "reviews.json"
}


def load_dataset_file(filename: str) -> List[Any]:
    path = DATA_DIR / filename
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[DB Engine] Error loading {filename}:", e)
    return []


@router.get("/status")
def get_database_services_status():
    mongo_status = check_mongodb_connection()
    postgres_status = check_postgresql_connection()
    
    available_datasets = {}
    total_records = 0
    for name, filename in DATASET_FILES.items():
        recs = load_dataset_file(filename)
        cnt = len(recs) if isinstance(recs, list) else 0
        available_datasets[name] = cnt
        total_records += cnt

    return {
        "status": "online",
        "services": {
            "mongodb": mongo_status,
            "postgresql": postgres_status,
            "localDiskJSONStorage": {
                "status": "online",
                "totalCollections": len(DATASET_FILES),
                "totalRecords": total_records,
                "dataDirectory": str(DATA_DIR)
            }
        },
        "datasetCounts": available_datasets
    }


@router.get("/collections")
def list_collections():
    summary = []
    for name, filename in DATASET_FILES.items():
        recs = load_dataset_file(filename)
        summary.append({
            "collection": name,
            "filename": filename,
            "count": len(recs) if isinstance(recs, list) else 0,
            "status": "connected"
        })
    return {
        "status": "success",
        "totalCollections": len(summary),
        "collections": summary
    }


@router.get("/collection/{collection_name}")
def get_collection_records(
    collection_name: str,
    search: Optional[str] = Query(None, description="Search term across records"),
    limit: Optional[int] = Query(50, ge=1, le=500)
):
    name_lower = collection_name.lower().strip()
    if name_lower not in DATASET_FILES:
        raise HTTPException(
            status_code=404, 
            detail=f"Collection '{collection_name}' not found. Available collections: {list(DATASET_FILES.keys())}"
        )

    # 1. Try MongoDB first if connected
    mongo_db = get_mongo_db()
    if mongo_db is not None:
        try:
            coll = mongo_db[name_lower]
            query_filter = {}
            if search:
                query_filter = {"$text": {"$search": search}}
            records = list(coll.find(query_filter, {"_id": 0}).limit(limit))
            if records:
                return {
                    "status": "success",
                    "source": "MongoDB Database",
                    "collection": name_lower,
                    "count": len(records),
                    "records": records
                }
        except Exception as e:
            print(f"[DB Query] Mongo query fallback for {name_lower}:", e)

    # 2. Disk JSON Storage Fallback
    records = load_dataset_file(DATASET_FILES[name_lower])
    if search and isinstance(records, list):
        q = search.lower()
        records = [r for r in records if q in json.dumps(r).lower()]

    records = records[:limit]

    return {
        "status": "success",
        "source": "JSON Database Engine",
        "collection": name_lower,
        "count": len(records),
        "records": records
    }


@router.post("/seed")
def trigger_database_seed():
    seed_result = seed_initial_datasets_to_mongodb()
    return {
        "status": "success",
        "message": "Database synchronization and seeding triggered",
        "mongodbSeed": seed_result
    }

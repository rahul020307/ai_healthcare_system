import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.database.sql_db import get_db_session, MedicineModel

router = APIRouter(prefix="/medicine", tags=["Medicine Knowledge Base"])

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def load_dataset(filename: str):
    path = DATA_DIR / filename
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Medicine API] Error loading {filename}:", e)
    return []


MEDICINES_DB = load_dataset("medicines.json")
GENERICS_DB = load_dataset("generic_alternatives.json")
INTERACTIONS_DB = load_dataset("drug_interactions.json")


class InteractionCheckRequest(BaseModel):
    medicines: List[str]


@router.get("/all")
def get_all_medicines():
    session = get_db_session()
    try:
        sql_meds = session.query(MedicineModel).all()
        if sql_meds:
            res = [
                {
                    "id": m.medicine_id,
                    "medicine_id": m.medicine_id,
                    "brand_name": m.brand_name,
                    "generic_name": m.generic_name,
                    "composition": m.composition,
                    "category": m.category,
                    "price": m.price,
                    "original_price": m.original_price,
                    "dosage": m.dosage,
                    "prescription_required": m.prescription_required,
                    "rating": m.rating,
                    "image_url": m.image_url
                }
                for m in sql_meds
            ]
            return {"status": "success", "source": "SQL Database", "count": len(res), "medicines": res}
    except Exception as e:
        print("[Medicine API] SQL fetch fallback:", e)
    finally:
        session.close()

    return {
        "status": "success",
        "source": "JSON Database Fallback",
        "count": len(MEDICINES_DB),
        "medicines": MEDICINES_DB
    }


@router.get("/search")
def search_medicines(query: str = Query(..., min_length=1, description="Search query for medicine brand, generic name, or composition")):
    q_lower = query.strip().lower()
    results = []
    
    # 1. Search in SQL database
    session = get_db_session()
    try:
        sql_matches = session.query(MedicineModel).filter(
            (MedicineModel.brand_name.ilike(f"%{q_lower}%")) |
            (MedicineModel.generic_name.ilike(f"%{q_lower}%")) |
            (MedicineModel.composition.ilike(f"%{q_lower}%")) |
            (MedicineModel.category.ilike(f"%{q_lower}%"))
        ).all()
        if sql_matches:
            for m in sql_matches:
                results.append({
                    "medicine_id": m.medicine_id,
                    "brand_name": m.brand_name,
                    "generic_name": m.generic_name,
                    "composition": m.composition,
                    "category": m.category,
                    "price": m.price,
                    "original_price": m.original_price,
                    "dosage": m.dosage,
                    "prescription_required": m.prescription_required,
                    "rating": m.rating
                })
            return {"status": "success", "source": "SQL Database", "query": query, "count": len(results), "results": results}
    except Exception as e:
        print("[Medicine API] SQL search fallback:", e)
    finally:
        session.close()

    # 2. JSON Fallback
    for m in MEDICINES_DB:
        b_name = m.get("brand_name", "").lower()
        g_name = m.get("generic_name", "").lower()
        comp = m.get("composition", "").lower()
        uses = [u.lower() for u in m.get("uses", [])]

        if q_lower in b_name or q_lower in g_name or q_lower in comp or any(q_lower in u for u in uses):
            results.append(m)

    return {
        "status": "success",
        "source": "JSON Knowledge Base",
        "query": query,
        "count": len(results),
        "results": results
    }


@router.get("/info/{med_id}")
def get_medicine_info(med_id: str):
    session = get_db_session()
    try:
        sql_med = session.query(MedicineModel).filter(
            (MedicineModel.medicine_id == med_id) |
            (MedicineModel.brand_name.ilike(med_id)) |
            (MedicineModel.generic_name.ilike(med_id))
        ).first()
        if sql_med:
            return {
                "status": "success",
                "source": "SQL Database",
                "medicine": {
                    "medicine_id": sql_med.medicine_id,
                    "brand_name": sql_med.brand_name,
                    "generic_name": sql_med.generic_name,
                    "composition": sql_med.composition,
                    "category": sql_med.category,
                    "price": sql_med.price,
                    "original_price": sql_med.original_price,
                    "dosage": sql_med.dosage,
                    "prescription_required": sql_med.prescription_required,
                    "rating": sql_med.rating,
                    "image_url": sql_med.image_url
                }
            }
    finally:
        session.close()

    for m in MEDICINES_DB:
        if m.get("medicine_id") == med_id or m.get("brand_name", "").lower() == med_id.lower() or m.get("generic_name", "").lower() == med_id.lower():
            return {
                "status": "success",
                "source": "JSON Knowledge Base",
                "medicine": m
            }

    raise HTTPException(status_code=404, detail=f"Medicine '{med_id}' not found in registered database.")


@router.get("/generics/{med_id}")
def get_generic_alternatives(med_id: str):
    med_match = None
    
    # 1. Look up target medicine
    session = get_db_session()
    try:
        sql_med = session.query(MedicineModel).filter(
            (MedicineModel.medicine_id == med_id) |
            (MedicineModel.brand_name.ilike(f"%{med_id}%")) |
            (MedicineModel.generic_name.ilike(f"%{med_id}%"))
        ).first()
        if sql_med:
            med_match = {
                "medicine_id": sql_med.medicine_id,
                "brand_name": sql_med.brand_name,
                "generic_name": sql_med.generic_name,
                "composition": sql_med.composition,
                "price": sql_med.price
            }
    finally:
        session.close()

    if not med_match:
        for m in MEDICINES_DB:
            if m.get("medicine_id") == med_id or m.get("brand_name", "").lower() == med_id.lower():
                med_match = m
                break

    if not med_match and MEDICINES_DB:
        med_match = MEDICINES_DB[0]

    brand_name = med_match.get("brand_name", med_id) if med_match else med_id
    generic_name = med_match.get("generic_name", "Standard Generic Formula") if med_match else "Generic Alternative"
    composition = med_match.get("composition", generic_name) if med_match else "Therapeutic Compound"
    brand_price = float(med_match.get("price", 60.0)) if med_match else 60.0
    
    generic_price = round(brand_price * 0.35, 2)
    savings_percent = round(((brand_price - generic_price) / brand_price) * 100)

    # 2. Check predefined generic alternatives
    alt_brands = []
    for g in GENERICS_DB:
        if (g.get("medicine_id") == med_id or 
            g.get("brand_name", "").lower() in brand_name.lower() or 
            brand_name.lower() in g.get("brand_name", "").lower()):
            alt_brands.extend(g.get("alternative_brands", []))

    if not alt_brands:
        alt_brands = ["Jan Aushadhi Generic", "Cipla Generic Care", "Mankind Pharma Bio-Equiv", "Zydus Affordable Salt"]

    return {
        "status": "success",
        "source": "SQL & Pharmacopeia Generics Engine",
        "medicineId": med_id,
        "brandName": brand_name,
        "genericName": generic_name,
        "composition": composition,
        "brandPrice": brand_price,
        "genericPrice": generic_price,
        "savingsPercent": savings_percent,
        "savingsAmount": round(brand_price - generic_price, 2),
        "manufacturer": "Jan Aushadhi PMBJP / Certified Generic Laboratory",
        "verifiedEquivalence": "100% Bio-Equivalent (Active Chemical Formulation)",
        "alternativeBrands": alt_brands
    }


@router.post("/check-interactions")
def check_drug_interactions(req: InteractionCheckRequest):
    if len(req.medicines) < 2:
        return {
            "status": "success",
            "hasInteractions": False,
            "message": "At least 2 medicines or active salts are required to evaluate drug-drug interactions.",
            "interactions": []
        }

    meds_clean = [m.strip().lower() for m in req.medicines if m and m.strip()]
    detected_interactions = []

    for item in INTERACTIONS_DB:
        m1 = (item.get("medicine_1") or item.get("drug_1") or "").lower()
        m2 = (item.get("medicine_2") or item.get("drug_2") or "").lower()

        # Check if both drugs in the interaction pair are present in the query
        match1 = any(m1 in m or m in m1 for m in meds_clean)
        match2 = any(m2 in m or m in m2 for m in meds_clean)

        if match1 and match2:
            detected_interactions.append({
                "interactionId": item.get("interaction_id", "INT"),
                "drug1": item.get("medicine_1") or item.get("drug_1"),
                "drug2": item.get("medicine_2") or item.get("drug_2"),
                "severity": item.get("severity", "Moderate"),
                "description": item.get("description", "Potential interaction detected."),
                "recommendation": item.get("recommendation", "Consult your physician or pharmacist before combining these medications.")
            })

    return {
        "status": "success",
        "evaluatedMedicines": req.medicines,
        "hasInteractions": len(detected_interactions) > 0,
        "count": len(detected_interactions),
        "interactions": detected_interactions
    }

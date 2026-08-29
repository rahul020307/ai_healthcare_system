import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List

from app.database.sql_db import get_db_session, MedicineModel

router = APIRouter(prefix="/medicine", tags=["Medicine Knowledge Base"])
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def load_dataset(filename: str):
    path = DATA_DIR / filename
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            print(f"[Medicine API] Error loading {filename}:", exc)
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
            medicines = [
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
                    "image_url": m.image_url,
                }
                for m in sql_meds
            ]
            return {"status": "success", "source": "SQL Database", "count": len(medicines), "medicines": medicines}
    except Exception as exc:
        print("[Medicine API] SQL fetch fallback:", exc)
    finally:
        session.close()

    return {"status": "success", "source": "JSON Database Fallback", "count": len(MEDICINES_DB), "medicines": MEDICINES_DB}


@router.get("/search")
def search_medicines(query: str = Query(..., min_length=1, description="Search query for medicine brand, generic name, or composition")):
    q_lower = query.strip().lower()
    results = []
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
                    "rating": m.rating,
                })
            return {"status": "success", "source": "SQL Database", "query": query, "count": len(results), "results": results}
    except Exception as exc:
        print("[Medicine API] SQL search fallback:", exc)
    finally:
        session.close()

    for medicine in MEDICINES_DB:
        brand = medicine.get("brand_name", "").lower()
        generic = medicine.get("generic_name", "").lower()
        composition = medicine.get("composition", "").lower()
        uses = [use.lower() for use in medicine.get("uses", [])]
        if q_lower in brand or q_lower in generic or q_lower in composition or any(q_lower in use for use in uses):
            results.append(medicine)

    return {"status": "success", "source": "JSON Knowledge Base", "query": query, "count": len(results), "results": results}


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
                    "image_url": sql_med.image_url,
                },
            }
    finally:
        session.close()

    for medicine in MEDICINES_DB:
        if (
            medicine.get("medicine_id") == med_id
            or medicine.get("brand_name", "").lower() == med_id.lower()
            or medicine.get("generic_name", "").lower() == med_id.lower()
        ):
            return {"status": "success", "source": "JSON Knowledge Base", "medicine": medicine}

    raise HTTPException(status_code=404, detail=f"Medicine '{med_id}' not found in registered database.")


@router.get("/generics/{med_id}")
def get_generic_alternatives(med_id: str):
    """Return only alternatives explicitly present in the curated generic dataset."""
    med_match = None
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
                "price": sql_med.price,
            }
    finally:
        session.close()

    if not med_match:
        for medicine in MEDICINES_DB:
            if (
                medicine.get("medicine_id") == med_id
                or medicine.get("brand_name", "").lower() == med_id.lower()
                or medicine.get("generic_name", "").lower() == med_id.lower()
            ):
                med_match = medicine
                break

    if not med_match:
        raise HTTPException(status_code=404, detail=f"Medicine '{med_id}' not found in registered database.")

    brand_name = med_match.get("brand_name", med_id)
    generic_name = med_match.get("generic_name", "")
    composition = med_match.get("composition", generic_name)
    brand_price = med_match.get("price")

    alternatives = []
    for generic in GENERICS_DB:
        if (
            generic.get("medicine_id") == med_id
            or generic.get("brand_name", "").lower() in brand_name.lower()
            or brand_name.lower() in generic.get("brand_name", "").lower()
        ):
            alternatives.extend(generic.get("alternative_brands", []))

    if not alternatives:
        return {
            "status": "success",
            "source": "Curated Generic Alternatives Dataset",
            "medicineId": med_id,
            "brandName": brand_name,
            "genericName": generic_name,
            "composition": composition,
            "brandPrice": brand_price,
            "genericPrice": None,
            "savingsPercent": None,
            "savingsAmount": None,
            "manufacturer": None,
            "verifiedEquivalence": None,
            "alternativeBrands": [],
            "message": "No curated generic alternative is registered for this medicine.",
        }

    return {
        "status": "success",
        "source": "Curated Generic Alternatives Dataset",
        "medicineId": med_id,
        "brandName": brand_name,
        "genericName": generic_name,
        "composition": composition,
        "brandPrice": brand_price,
        "genericPrice": None,
        "savingsPercent": None,
        "savingsAmount": None,
        "manufacturer": None,
        "verifiedEquivalence": None,
        "alternativeBrands": alternatives,
        "message": "Alternatives are listed from the application's curated dataset. Equivalence, price, manufacturer, and stock are not independently verified by this API.",
    }


@router.post("/check-interactions")
def check_drug_interactions(req: InteractionCheckRequest):
    if len(req.medicines) < 2:
        return {
            "status": "success",
            "hasInteractions": False,
            "message": "At least 2 medicines or active salts are required to evaluate drug-drug interactions.",
            "interactions": [],
        }

    medicines = [medicine.strip().lower() for medicine in req.medicines if medicine and medicine.strip()]
    detected = []

    for item in INTERACTIONS_DB:
        m1 = (item.get("medicine_1") or item.get("drug_1") or "").lower()
        m2 = (item.get("medicine_2") or item.get("drug_2") or "").lower()
        match1 = any(m1 in medicine or medicine in m1 for medicine in medicines)
        match2 = any(m2 in medicine or medicine in m2 for medicine in medicines)
        if match1 and match2:
            detected.append({
                "interactionId": item.get("interaction_id", "INT"),
                "drug1": item.get("medicine_1") or item.get("drug_1"),
                "drug2": item.get("medicine_2") or item.get("drug_2"),
                "severity": item.get("severity", "Moderate"),
                "description": item.get("description", "Potential interaction detected."),
                "recommendation": item.get("recommendation", "Consult your physician or pharmacist before combining these medications."),
            })

    return {
        "status": "success",
        "evaluatedMedicines": req.medicines,
        "hasInteractions": bool(detected),
        "count": len(detected),
        "interactions": detected,
    }

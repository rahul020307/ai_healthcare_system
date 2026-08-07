import json
import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/medicine", tags=["Medicine Knowledge Base"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def load_dataset(filename: str):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filename}:", e)
    return []


MEDICINES_DB = load_dataset("medicines.json")
GENERICS_DB = load_dataset("generic_alternatives.json")
INTERACTIONS_DB = load_dataset("drug_interactions.json")


class InteractionCheckRequest(BaseModel):
    medicines: List[str]


@router.get("/all")
def get_all_medicines():
    return {
        "status": "success",
        "count": len(MEDICINES_DB),
        "medicines": MEDICINES_DB
    }


@router.get("/search")
def search_medicines(query: str = Query(..., min_length=1, description="Search query for medicine brand, generic name, or composition")):
    q_lower = query.strip().lower()
    results = []
    for m in MEDICINES_DB:
        b_name = m.get("brand_name", "").lower()
        g_name = m.get("generic_name", "").lower()
        comp = m.get("composition", "").lower()
        uses = [u.lower() for u in m.get("uses", [])]

        if q_lower in b_name or q_lower in g_name or q_lower in comp or any(q_lower in u for u in uses):
            results.append(m)

    return {
        "status": "success",
        "query": query,
        "count": len(results),
        "results": results
    }


@router.get("/info/{med_id}")
def get_medicine_info(med_id: str):
    for m in MEDICINES_DB:
        if m.get("medicine_id") == med_id or m.get("brand_name", "").lower() == med_id.lower() or m.get("generic_name", "").lower() == med_id.lower():
            return {
                "status": "success",
                "medicine": m
            }

    # If not found directly by ID, return first match or 404
    raise HTTPException(status_code=404, detail=f"Medicine '{med_id}' not found in registered database.")


@router.get("/generics/{med_id}")
def get_generic_alternatives(med_id: str):
    med_match = None
    for m in MEDICINES_DB:
        if m.get("medicine_id") == med_id or m.get("brand_name", "").lower() == med_id.lower():
            med_match = m
            break

    if not med_match and MEDICINES_DB:
        med_match = MEDICINES_DB[0]

    alt_generics = []
    for g in GENERICS_DB:
        if g.get("brand_medicine_id") == med_id or g.get("composition", "").lower() in med_match.get("composition", "").lower():
            alt_generics.append(g)

    # If no direct generic record match, construct generic recommendation
    if not alt_generics and med_match:
        price = med_match.get("price", 50.0)
        generic_price = round(price * 0.4, 2)
        alt_generics.append({
            "generic_id": f"gen-alt-{med_match.get('medicine_id', '001')}",
            "brand_name": med_match.get("brand_name"),
            "generic_name": med_match.get("generic_name"),
            "composition": med_match.get("composition"),
            "generic_price": generic_price,
            "brand_price": price,
            "savings_percent": 60,
            "manufacturer": "Jan Aushadhi / Certified Generic Lab"
        })

    return {
        "status": "success",
        "medicineId": med_id,
        "brandName": med_match.get("brand_name") if med_match else med_id,
        "genericAlternatives": alt_generics
    }


@router.post("/check-interactions")
def check_drug_interactions(req: InteractionCheckRequest):
    if len(req.medicines) < 2:
        return {
            "status": "success",
            "hasInteractions": False,
            "message": "At least 2 medicines are required to evaluate drug-drug interactions.",
            "interactions": []
        }

    meds_lower = [m.strip().lower() for m in req.medicines]
    detected_interactions = []

    for item in INTERACTIONS_DB:
        m1 = item.get("drug_1", "").lower()
        m2 = item.get("drug_2", "").lower()

        if any(m1 in d for d in meds_lower) and any(m2 in d for d in meds_lower):
            detected_interactions.append(item)

    return {
        "status": "success",
        "evaluatedMedicines": req.medicines,
        "hasInteractions": len(detected_interactions) > 0,
        "count": len(detected_interactions),
        "interactions": detected_interactions
    }

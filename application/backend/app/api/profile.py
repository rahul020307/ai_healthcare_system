import json
from pathlib import Path
from fastapi import APIRouter, Body

router = APIRouter(prefix="/profile", tags=["Profile"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def load_records():
    file_path = DATA_DIR / "health_records.json"
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_records(records):
    file_path = DATA_DIR / "health_records.json"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
            return True
    except Exception as e:
        print("Error saving health_records.json:", e)
        return False


@router.get("/user")
def get_user_profile():
    return {
        "status": "success",
        "user": {
            "name": "Rahul Sharma",
            "verified": True,
            "phone": "+91 98765 43210",
            "email": "rahul.sharma@email.com",
            "location": "Hyderabad, Telangana",
            "age": 34,
            "gender": "Male",
            "bloodGroup": "O+",
            "familyMembers": [
                {"id": "fam1", "name": "Rahul Sharma", "relation": "Self"},
                {"id": "fam2", "name": "Eleanor Sharma", "relation": "Mother"},
                {"id": "fam3", "name": "Sarah Sharma", "relation": "Wife"},
                {"id": "fam4", "name": "Leo Sharma", "relation": "Son"}
            ]
        }
    }


@router.get("/health-records")
def get_health_records():
    return {
        "status": "success",
        "records": load_records()
    }


@router.post("/upload-record")
def upload_health_record(payload: dict = Body(...)):
    records = load_records()
    new_record = {
        "id": payload.get("id") or f"rec-{int(Path(__file__).stat().st_mtime * 1000)}",
        "memberId": payload.get("memberId", "mem-1"),
        "title": payload.get("title", "Uploaded Health Document"),
        "category": payload.get("category", "Medical Reports"),
        "date": payload.get("date") or "2026-08-07",
        "doctor": payload.get("doctor", "Self Upload / Clinic"),
        "facility": payload.get("facility", "CuraAssist Digital Hub"),
        "tags": payload.get("tags", ["Uploaded", "Health Record"]),
        "summary": payload.get("summary", "Uploaded medical document saved successfully.")
    }
    records.insert(0, new_record)
    saved = save_records(records)
    return {
        "status": "success" if saved else "error",
        "message": "Health record permanently saved to dataset",
        "record": new_record
    }

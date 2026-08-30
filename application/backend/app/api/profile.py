import json
import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Body, Depends, HTTPException

from app.auth import get_current_user
from app.database.sql_db import (
    get_db_session,
    UserModel,
    HealthRecordModel,
    AppointmentModel,
    VitalRecordModel,
    MedicineScheduleModel,
)
from app.services.storage import upload_base64_to_supabase

router = APIRouter(prefix="/profile", tags=["Profile"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"


# --- USER PROFILE ENDPOINTS (SQL BACKED) ---

@router.get("/user")
def get_user_profile(current_user: UserModel = Depends(get_current_user)):
    return {
        "status": "success",
        "source": "SQL Database",
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "verified": True,
            "phone": current_user.phone,
            "email": current_user.email,
            "location": current_user.location,
            "age": current_user.age,
            "gender": current_user.gender,
            "bloodGroup": current_user.blood_group,
            "role": current_user.role,
            "familyMembers": [
                {"id": "fam1", "name": current_user.name, "relation": "Self"},
                {"id": "fam2", "name": "Eleanor Sharma", "relation": "Mother"},
                {"id": "fam3", "name": "Sarah Sharma", "relation": "Wife"},
                {"id": "fam4", "name": "Leo Sharma", "relation": "Son"},
            ],
        },
    }


@router.put("/user")
def update_user_profile(
    payload: dict = Body(...),
    current_user: UserModel = Depends(get_current_user),
):
    session = get_db_session()
    try:
        user = session.query(UserModel).filter_by(id=current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Authenticated user profile not found")

        if "name" in payload and payload["name"]:
            user.name = payload["name"]
        if "email" in payload and payload["email"]:
            user.email = payload["email"]
        if "phone" in payload and payload["phone"]:
            user.phone = payload["phone"]
        if "location" in payload and payload["location"]:
            user.location = payload["location"]
        if "age" in payload and payload["age"]:
            try:
                user.age = int(payload["age"])
            except (ValueError, TypeError):
                pass
        if "gender" in payload and payload["gender"]:
            user.gender = payload["gender"]
        if "bloodGroup" in payload and payload["bloodGroup"]:
            user.blood_group = payload["bloodGroup"]

        session.commit()
        return {
            "status": "success",
            "message": "Profile updated in SQL database",
            "user": {
                "id": user.id,
                "name": user.name,
                "phone": user.phone,
                "email": user.email,
                "location": user.location,
                "age": user.age,
                "gender": user.gender,
                "bloodGroup": user.blood_group,
                "role": user.role,
            },
        }
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# --- HEALTH RECORDS ENDPOINTS (SQL BACKED) ---

@router.get("/health-records")
def get_health_records(current_user: UserModel = Depends(get_current_user)):
    session = get_db_session()
    try:
        records = (
            session.query(HealthRecordModel)
            .filter(HealthRecordModel.owner_user_id == current_user.id)
            .order_by(HealthRecordModel.created_at.desc())
            .all()
        )
        res = []
        for r in records:
            res.append({
                "id": r.id,
                "memberId": r.member_id,
                "title": r.title,
                "category": r.category,
                "date": r.date,
                "doctor": r.doctor,
                "facility": r.facility,
                "summary": r.summary,
                "tags": [t.strip() for t in r.tags.split(",") if t.strip()] if r.tags else ["Health Record"],
            })
        return {
            "status": "success",
            "source": "SQL Database",
            "count": len(res),
            "records": res,
        }
    finally:
        session.close()


@router.post("/upload-record")
def upload_health_record(
    payload: dict = Body(...),
    current_user: UserModel = Depends(get_current_user),
):
    session = get_db_session()
    try:
        rec_id = payload.get("id") or f"rec-{int(datetime.datetime.utcnow().timestamp() * 1000)}"
        tags_raw = payload.get("tags", ["Uploaded", "Health Record"])
        tags_str = ",".join(tags_raw) if isinstance(tags_raw, list) else str(tags_raw)

        file_url = payload.get("file_url") or payload.get("fileUrl")
        file_data = payload.get("fileData") or payload.get("base64")
        if file_data and not file_url:
            filename = payload.get("filename") or f"prescription_{rec_id}.jpg"
            storage_res = upload_base64_to_supabase(
                base64_data=file_data,
                filename=filename,
                user_id=current_user.id,
            )
            file_url = storage_res.get("file_url")

        new_rec = HealthRecordModel(
            id=rec_id,
            owner_user_id=current_user.id,
            member_id=payload.get("memberId", "fam1"),
            user_email=current_user.email,
            title=payload.get("title", "Uploaded Health Document"),
            category=payload.get("category", "Medical Reports"),
            date=payload.get("date") or datetime.date.today().isoformat(),
            doctor=payload.get("doctor", "Self Upload / Clinic"),
            facility=payload.get("facility", "CuraAssist Digital Hub"),
            tags=tags_str,
            summary=payload.get("summary", "Medical record stored securely in Supabase / SQL database."),
            file_url=file_url,
        )
        session.add(new_rec)
        session.commit()

        return {
            "status": "success",
            "message": "Health record permanently stored in SQL database",
            "record": {
                "id": new_rec.id,
                "memberId": new_rec.member_id,
                "title": new_rec.title,
                "category": new_rec.category,
                "date": new_rec.date,
                "doctor": new_rec.doctor,
                "facility": new_rec.facility,
                "tags": tags_raw,
                "summary": new_rec.summary,
                "file_url": new_rec.file_url,
            },
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.delete("/health-records/{record_id}")
def delete_health_record(
    record_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    session = get_db_session()
    try:
        rec = (
            session.query(HealthRecordModel)
            .filter(
                HealthRecordModel.id == record_id,
                HealthRecordModel.owner_user_id == current_user.id,
            )
            .first()
        )
        if not rec:
            raise HTTPException(status_code=404, detail="Health record not found or unauthorized")
        session.delete(rec)
        session.commit()
        return {"status": "success", "message": "Health record deleted", "id": record_id}
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# --- APPOINTMENTS ENDPOINTS (SQL BACKED) ---

@router.get("/appointments")
def get_appointments(current_user: UserModel = Depends(get_current_user)):
    session = get_db_session()
    try:
        appts = (
            session.query(AppointmentModel)
            .filter(AppointmentModel.owner_user_id == current_user.id)
            .order_by(AppointmentModel.created_at.desc())
            .all()
        )
        res = []
        for a in appts:
            res.append({
                "id": a.id,
                "doctorId": a.doctor_id,
                "doctorName": a.doctor_name,
                "specialty": a.specialty,
                "patientName": a.patient_name,
                "date": a.appointment_date,
                "time": a.appointment_time,
                "status": a.status,
                "type": a.consultation_type,
                "hospitalName": a.hospital_name,
                "notes": a.notes,
            })
        return {"status": "success", "source": "SQL Database", "count": len(res), "appointments": res}
    finally:
        session.close()


@router.post("/appointments")
def book_appointment(
    payload: dict = Body(...),
    current_user: UserModel = Depends(get_current_user),
):
    session = get_db_session()
    try:
        appt_id = payload.get("id") or f"apt-{int(datetime.datetime.utcnow().timestamp() * 1000)}"
        appt = AppointmentModel(
            id=appt_id,
            owner_user_id=current_user.id,
            user_email=current_user.email,
            doctor_id=payload.get("doctorId", "doc-01"),
            doctor_name=payload.get("doctorName", "Dr. Priya Sharma"),
            specialty=payload.get("specialty", "Cardiologist"),
            patient_name=payload.get("patientName", current_user.name),
            appointment_date=payload.get("date", datetime.date.today().isoformat()),
            appointment_time=payload.get("time", "10:30 AM"),
            status=payload.get("status", "Confirmed"),
            consultation_type=payload.get("type", "In-Person"),
            hospital_name=payload.get("hospitalName", "Apollo Hospitals"),
            notes=payload.get("notes", "Regular Consultation"),
        )
        session.add(appt)
        session.commit()

        return {
            "status": "success",
            "message": "Appointment booked and stored in SQL database",
            "appointment": {
                "id": appt.id,
                "doctorName": appt.doctor_name,
                "specialty": appt.specialty,
                "patientName": appt.patient_name,
                "date": appt.appointment_date,
                "time": appt.appointment_time,
                "status": appt.status,
                "hospitalName": appt.hospital_name,
            },
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.delete("/appointments/{appt_id}")
def cancel_appointment(
    appt_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    session = get_db_session()
    try:
        appt = (
            session.query(AppointmentModel)
            .filter(
                AppointmentModel.id == appt_id,
                AppointmentModel.owner_user_id == current_user.id,
            )
            .first()
        )
        if appt:
            session.delete(appt)
            session.commit()
            return {"status": "success", "message": f"Appointment {appt_id} cancelled"}
        return {"status": "success", "message": "Appointment not found or already cancelled"}
    finally:
        session.close()


# --- VITALS LOGGING ENDPOINTS (SQL BACKED) ---

@router.get("/vitals")
def get_user_vitals(current_user: UserModel = Depends(get_current_user)):
    session = get_db_session()
    try:
        vitals = (
            session.query(VitalRecordModel)
            .filter(VitalRecordModel.owner_user_id == current_user.id)
            .order_by(VitalRecordModel.recorded_at.desc())
            .limit(30)
            .all()
        )
        res = []
        for v in vitals:
            res.append({
                "id": v.id,
                "systolic": v.systolic,
                "diastolic": v.diastolic,
                "pulse": v.pulse,
                "temperature": v.temperature,
                "glucose": v.glucose,
                "recordedAt": v.recorded_at.isoformat() if v.recorded_at else datetime.datetime.utcnow().isoformat(),
            })
        return {"status": "success", "source": "SQL Database", "count": len(res), "vitals": res}
    finally:
        session.close()


@router.post("/vitals")
def log_vital_reading(
    payload: dict = Body(...),
    current_user: UserModel = Depends(get_current_user),
):
    session = get_db_session()
    try:
        vital_id = payload.get("id") or f"vit-{int(datetime.datetime.utcnow().timestamp() * 1000)}"
        vital = VitalRecordModel(
            id=vital_id,
            owner_user_id=current_user.id,
            user_email=current_user.email,
            systolic=int(payload.get("systolic", 120)),
            diastolic=int(payload.get("diastolic", 80)),
            pulse=int(payload.get("pulse", 72)),
            temperature=float(payload.get("temperature", 98.6)),
            glucose=float(payload.get("glucose", 95.0)),
        )
        session.add(vital)
        session.commit()
        vital_payload = dict(payload)
        vital_payload["id"] = vital_id
        return {"status": "success", "message": "Vitals logged into SQL database", "vital": vital_payload}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# --- AUTH & USER REGISTRATION ---
# Legacy compatibility endpoints remain separate from the Supabase JWT flow.
# They do not create or authorize API bearer tokens.

@router.post("/login")
def login_user(payload: dict = Body(...)):
    identity = payload.get("identity") or payload.get("email") or "User"
    email = payload.get("email") or f"{identity.replace(' ', '.').lower()}@curaassist.health"
    name = identity.split("@")[0].capitalize()

    session = get_db_session()
    try:
        user = session.query(UserModel).filter_by(email=email).first()
        if not user:
            user = UserModel(
                id=f"usr-{int(datetime.datetime.utcnow().timestamp())}",
                name=name,
                email=email,
                role=payload.get("role", "Patient"),
            )
            session.add(user)
            session.commit()

        return {
            "status": "success",
            "message": "Legacy login compatibility endpoint. Use Supabase Auth for API authentication.",
            "token": None,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "bloodGroup": user.blood_group,
            },
        }
    finally:
        session.close()


@router.post("/register")
def register_user(payload: dict = Body(...)):
    name = payload.get("name") or "New User"
    email = payload.get("email") or "user@curaassist.health"

    session = get_db_session()
    try:
        user = session.query(UserModel).filter_by(email=email).first()
        if not user:
            user = UserModel(
                id=f"usr-{int(datetime.datetime.utcnow().timestamp())}",
                name=name,
                email=email,
                phone=payload.get("phone", "+91 98765 43210"),
                location=payload.get("location", "Hyderabad, Telangana"),
                blood_group=payload.get("bloodGroup", "O+"),
                role=payload.get("role", "Patient"),
            )
            session.add(user)
            session.commit()

        return {
            "status": "success",
            "message": f"Registration Complete for {name}. Use Supabase Auth for sign-in.",
            "token": None,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "bloodGroup": user.blood_group,
            },
        }
    finally:
        session.close()


# --- UPLOADS STORAGE & SCAN LOGS ---

UPLOADS_FILE = DATA_DIR / "user_scanned_uploads.json"


def load_uploads():
    if UPLOADS_FILE.exists():
        try:
            with open(UPLOADS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_uploads(uploads):
    try:
        with open(UPLOADS_FILE, "w", encoding="utf-8") as f:
            json.dump(uploads, f, indent=2)
            return True
    except Exception as e:
        print("Error saving user_scanned_uploads.json:", e)
        return False


@router.get("/uploads")
def get_user_uploads(current_user: UserModel = Depends(get_current_user)):
    # The legacy JSON upload store has no ownership column. Keep it out of the
    # authenticated data surface until it is migrated to owner_user_id storage.
    return {"status": "success", "uploads": []}


@router.post("/uploads")
def save_user_upload(
    payload: dict = Body(...),
    current_user: UserModel = Depends(get_current_user),
):
    uploads = load_uploads()
    item = {
        "id": payload.get("id") or f"up-{int(datetime.datetime.utcnow().timestamp() * 1000)}",
        "fileName": payload.get("fileName", "scanned_doc.png"),
        "fileType": payload.get("fileType", "image/png"),
        "uploadDate": payload.get("uploadDate", datetime.date.today().isoformat()),
        "category": payload.get("category", "Prescription Scan"),
        "previewUrl": payload.get("previewUrl") or payload.get("fileBase64") or "",
        "extractedText": payload.get("extractedText", ""),
        "aiSummary": payload.get("aiSummary", ""),
        "matchedMedicines": payload.get("matchedMedicines", []),
        "ownerUserId": current_user.id,
    }
    uploads.insert(0, item)
    save_uploads(uploads)
    return {"status": "success", "message": "Upload stored in backend database", "upload": item}


@router.delete("/uploads/{upload_id}")
def delete_user_upload(
    upload_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    uploads = load_uploads()
    updated = [
        u for u in uploads
        if not (u.get("id") == upload_id and u.get("ownerUserId") == current_user.id)
    ]
    save_uploads(updated)
    return {"status": "success", "message": "Upload record deleted"}


# --- MEDICINE SCHEDULE ENDPOINTS (SQL / SUPABASE BACKED) ---

@router.get("/schedules")
def get_medicine_schedules(current_user: UserModel = Depends(get_current_user)):
    session = get_db_session()
    try:
        schedules = (
            session.query(MedicineScheduleModel)
            .filter(MedicineScheduleModel.owner_user_id == current_user.id)
            .order_by(MedicineScheduleModel.created_at.desc())
            .all()
        )
        res = []
        for s in schedules:
            res.append({
                "id": s.id,
                "name": s.name,
                "dosage": s.dosage,
                "frequency": s.frequency,
                "time": s.time,
                "category": s.category,
                "nextDose": s.next_dose,
                "status": s.status,
            })
        return {
            "status": "success",
            "source": "SQL Database",
            "count": len(res),
            "schedules": res,
        }
    finally:
        session.close()


@router.post("/schedules")
def add_medicine_schedule(
    payload: dict = Body(...),
    current_user: UserModel = Depends(get_current_user),
):
    session = get_db_session()
    try:
        sch_id = payload.get("id") or f"sch-{int(datetime.datetime.utcnow().timestamp() * 1000)}"
        item = MedicineScheduleModel(
            id=sch_id,
            owner_user_id=current_user.id,
            user_email=current_user.email,
            name=payload.get("name", "Prescription Medicine"),
            dosage=payload.get("dosage", "1 Tablet"),
            frequency=payload.get("frequency", "Daily"),
            time=payload.get("time", "08:00 AM"),
            category=payload.get("category", "General"),
            next_dose=payload.get("nextDose") or payload.get("next_dose", "Today, 08:00 AM"),
            status=payload.get("status", "Active"),
        )
        session.add(item)
        session.commit()
        out_payload = dict(payload)
        out_payload["id"] = sch_id
        return {"status": "success", "message": "Medicine schedule saved", "schedule": out_payload}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@router.delete("/schedules/{schedule_id}")
def delete_medicine_schedule(
    schedule_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    session = get_db_session()
    try:
        item = (
            session.query(MedicineScheduleModel)
            .filter(
                MedicineScheduleModel.id == schedule_id,
                MedicineScheduleModel.owner_user_id == current_user.id,
            )
            .first()
        )
        if not item:
            raise HTTPException(status_code=404, detail="Schedule entry not found or unauthorized")
        session.delete(item)
        session.commit()
        return {"status": "success", "message": "Schedule entry deleted", "id": schedule_id}
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

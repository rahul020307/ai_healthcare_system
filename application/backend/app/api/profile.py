import json
import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.database.sql_db import (
    get_db_session,
    UserModel,
    HealthRecordModel,
    AppointmentModel,
    VitalRecordModel,
    MedicineScheduleModel,
)
from app.services.storage import upload_base64_to_supabase, upload_avatar_to_supabase, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
import requests

router = APIRouter(prefix="/profile", tags=["Profile"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _sync_supabase_profile(user_id: str, updates: dict) -> None:
    """Sync profile updates directly to Supabase Postgres public.users by Auth UUID."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY or "placeholder" in SUPABASE_URL:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?auth_user_id=eq.{user_id}"
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        db_payload = {}
        if "name" in updates:
            db_payload["name"] = updates["name"]
        if "phone" in updates:
            db_payload["phone"] = updates["phone"]
        if "location" in updates:
            db_payload["location"] = updates["location"]
        if "age" in updates:
            try:
                db_payload["age"] = int(updates["age"])
            except Exception:
                pass

        if "gender" in updates:
            db_payload["gender"] = updates["gender"]
        if "bloodGroup" in updates:
            db_payload["blood_group"] = updates["bloodGroup"]
        if "avatar_url" in updates:
            db_payload["avatar_url"] = updates["avatar_url"]

        if db_payload:
            requests.patch(url, json=db_payload, headers=headers, timeout=5)
    except Exception as e:
        print("[Supabase Sync] Note:", e)

import re

# --- SUPABASE-BACKED USER PROFILE & AVATAR API ---

@router.get("/user")
def get_user_profile(current_user: UserModel = Depends(get_current_user)):
    return {
        "status": "success",
        "source": "SQL Database + Supabase",
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
            "avatar": current_user.avatar_url,
            "avatarUrl": current_user.avatar_url,
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

        if "name" in payload:
            user.name = str(payload["name"]).strip() or user.name
        if "phone" in payload:
            user.phone = str(payload["phone"]).strip()
        if "location" in payload:
            user.location = str(payload["location"]).strip()
        if "age" in payload:
            try:
                user.age = int(payload["age"])
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Age must be a valid integer")
        if "gender" in payload:
            user.gender = str(payload["gender"]).strip() or user.gender
        if "bloodGroup" in payload:
            user.blood_group = str(payload["bloodGroup"]).strip() or user.blood_group

        session.commit()
        session.refresh(user)
        _sync_supabase_profile(
            str(current_user.auth_user_id or current_user.id),
            {
                "name": user.name,
                "phone": user.phone,
                "location": user.location,
                "age": user.age,
                "gender": user.gender,
                "bloodGroup": user.blood_group,
            },
        )

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
                "avatar": user.avatar_url,
                "avatarUrl": user.avatar_url,
            },
        }
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Unable to update profile") from exc
    finally:
        session.close()


class AvatarUploadPayload(BaseModel):
    data: str
    filename: str = "avatar.jpg"


@router.post("/avatar")
def upload_user_avatar(
    payload: AvatarUploadPayload,
    current_user: UserModel = Depends(get_current_user),
):
    avatar_data = (payload.data or "").strip()
    if not avatar_data:
        raise HTTPException(status_code=400, detail="Avatar data is required")
    if not avatar_data.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="Avatar must be an image data URL")

    # Reject oversized encoded payloads before decoding. 5 MB is the configured
    # avatar-object limit; this threshold keeps request size bounded as well.
    if len(avatar_data) > 7 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Avatar exceeds the 5 MB upload limit")

    try:
        public_url = upload_avatar_to_supabase(
            base64_data=avatar_data,
            user_id=str(current_user.auth_user_id or current_user.id),
            filename=payload.filename or "avatar.jpg",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to store avatar in Supabase Storage") from exc

    if not public_url or public_url.startswith("data:"):
        raise HTTPException(status_code=502, detail="Supabase Storage did not return a persistent avatar URL")

    session = get_db_session()
    try:
        user = session.query(UserModel).filter_by(id=current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Authenticated user profile not found")

        user.avatar_url = public_url
        session.commit()
        session.refresh(user)
        _sync_supabase_profile(
            str(current_user.auth_user_id or current_user.id),
            {"avatar_url": public_url},
        )

        return {
            "status": "success",
            "message": "Avatar uploaded to Supabase Storage and profile updated",
            "user": {
                "id": user.id,
                "avatar": public_url,
                "avatarUrl": public_url,
            },
        }
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Unable to persist avatar profile URL") from exc
    finally:
        session.close()

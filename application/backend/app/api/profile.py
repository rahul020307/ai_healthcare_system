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

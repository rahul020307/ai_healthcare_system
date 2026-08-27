import os
import uuid
import base64
import requests
from typing import Optional, Dict, Any

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY", "")
DEFAULT_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "prescriptions")


def upload_file_to_supabase(
    file_bytes: bytes,
    filename: str,
    user_id: str,
    content_type: str = "image/jpeg",
    bucket_name: str = DEFAULT_BUCKET,
) -> Dict[str, Any]:
    """
    Uploads a file to Supabase Storage under isolated path users/<user_id>/<file_id>_<filename>.
    Returns storage metadata including public/signed file URL.
    """
    clean_filename = os.path.basename(filename).replace(" ", "_")
    file_id = f"file-{uuid.uuid4().hex[:8]}"
    storage_path = f"users/{user_id}/{file_id}_{clean_filename}"

    if not SUPABASE_URL or not SUPABASE_KEY:
        # Fallback for environments without live Supabase storage credentials
        local_url = f"/uploads/{storage_path}"
        return {
            "status": "success",
            "storage": "local_fallback",
            "bucket": bucket_name,
            "path": storage_path,
            "file_url": local_url,
            "filename": filename,
        }

    upload_url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{storage_path}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": content_type,
        "x-upsert": "true",
    }

    try:
        response = requests.post(upload_url, data=file_bytes, headers=headers, timeout=10)
        response.raise_for_status()

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{storage_path}"
        return {
            "status": "success",
            "storage": "supabase",
            "bucket": bucket_name,
            "path": storage_path,
            "file_url": public_url,
            "filename": filename,
        }
    except Exception as exc:
        print(f"[Supabase Storage] Upload error for {storage_path}:", exc)
        fallback_url = f"/uploads/{storage_path}"
        return {
            "status": "partial",
            "storage": "local_fallback",
            "bucket": bucket_name,
            "path": storage_path,
            "file_url": fallback_url,
            "filename": filename,
            "error": str(exc),
        }


def upload_base64_to_supabase(
    base64_data: str,
    filename: str,
    user_id: str,
    bucket_name: str = DEFAULT_BUCKET,
) -> Dict[str, Any]:
    """Helper to upload base64 encoded data to Supabase Storage."""
    if "," in base64_data:
        header, encoded = base64_data.split(",", 1)
        mime = header.split(";")[0].replace("data:", "") if "data:" in header else "image/jpeg"
    else:
        encoded = base64_data
        mime = "image/jpeg"

    try:
        file_bytes = base64.b64decode(encoded)
    except Exception as exc:
        raise ValueError("Invalid base64 string provided") from exc

    return upload_file_to_supabase(
        file_bytes=file_bytes,
        filename=filename,
        user_id=user_id,
        content_type=mime,
        bucket_name=bucket_name,
    )


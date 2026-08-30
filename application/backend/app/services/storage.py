import os
import uuid
import base64
import requests
from typing import Dict, Any

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ifwsijbkmuzqttwbvifp.supabase.co").strip().rstrip("/")
# Storage operations must use the service role key. Never fall back to an anon key
# because the health-record bucket is private and uploads are server-authorized.
SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlmd3NpamJrbXV6cXR0d2J2aWZwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NzYyMzYxMiwiZXhwIjoyMTAzMTk5NjEyfQ.GKXAePSTNPWMvW6tddHy6pTTBV21BipSI846B2bSZCc"
).strip()
DEFAULT_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "health-records").strip() or "health-records"
MAX_FILE_BYTES = 20 * 1024 * 1024


def _headers(content_type: str = "application/json") -> Dict[str, str]:
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required for private health-record storage")
    return {
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Content-Type": content_type,
    }


def _signed_url(bucket_name: str, storage_path: str, expires_in: int = 3600) -> str:
    """Create a short-lived signed URL for a private Storage object."""
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is required for private health-record storage")

    sign_url = f"{SUPABASE_URL}/storage/v1/object/sign/{bucket_name}/{storage_path}"
    response = requests.post(
        sign_url,
        json={"expiresIn": expires_in},
        headers=_headers(),
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    signed_path = payload.get("signedURL") or payload.get("signedUrl")
    if not signed_path:
        raise RuntimeError("Supabase Storage did not return a signed URL")
    if signed_path.startswith("http"):
        return signed_path
    return f"{SUPABASE_URL}/storage/v1{signed_path}"


def upload_file_to_supabase(
    file_bytes: bytes,
    filename: str,
    user_id: str,
    content_type: str = "image/jpeg",
    bucket_name: str = DEFAULT_BUCKET,
) -> Dict[str, Any]:
    """Upload a private health document under users/<user_id>/ and return a signed URL (or local URL fallback)."""
    if len(file_bytes) > MAX_FILE_BYTES:
        raise ValueError("File exceeds the 20 MB health-record upload limit")

    clean_filename = os.path.basename(filename).replace(" ", "_")
    file_id = f"file-{uuid.uuid4().hex[:8]}"
    storage_path = f"users/{user_id}/{file_id}_{clean_filename}"

    # 1. Upload to Supabase Storage if configured
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY and not ("placeholder" in SUPABASE_URL or "curaassist-carehub.supabase.co" in SUPABASE_URL):
        try:
            upload_url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{storage_path}"
            headers = _headers(content_type)
            headers["x-upsert"] = "false"

            response = requests.post(
                upload_url,
                data=file_bytes,
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()

            return {
                "status": "success",
                "storage": "supabase_private",
                "bucket": bucket_name,
                "path": storage_path,
                "file_url": _signed_url(bucket_name, storage_path),
                "filename": filename,
            }
        except Exception as e:
            print("[Storage] Supabase upload failed, falling back to local:", e)

    # 2. Local resilient storage fallback for offline / development
    try:
        from pathlib import Path
        uploads_dir = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        local_path = uploads_dir / f"{file_id}_{clean_filename}"
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        
        # Also generate inline data URL preview
        b64_str = base64.b64encode(file_bytes).decode("utf-8")
        data_url = f"data:{content_type};base64,{b64_str}"
        return {
            "status": "success",
            "storage": "local_fallback",
            "bucket": "local",
            "path": str(local_path),
            "file_url": data_url,
            "filename": filename,
        }
    except Exception as exc:
        raise RuntimeError("Unable to store health record document") from exc


def _guess_mime_type(filename: str, fallback: str = "image/jpeg") -> str:
    ext = os.path.splitext(filename)[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
    }
    return mime_map.get(ext, fallback)


def upload_base64_to_supabase(
    base64_data: str,
    filename: str,
    user_id: str,
    bucket_name: str = DEFAULT_BUCKET,
) -> Dict[str, Any]:
    """Decode base64 data and upload it to the private health-record bucket (supports PDF, JPG, PNG, WEBP, DOC)."""
    if "," in base64_data:
        header, encoded = base64_data.split(",", 1)
        mime = header.split(";")[0].replace("data:", "") if "data:" in header else _guess_mime_type(filename)
    else:
        encoded = base64_data
        mime = _guess_mime_type(filename)

    try:
        file_bytes = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("Invalid base64 string provided") from exc

    return upload_file_to_supabase(
        file_bytes=file_bytes,
        filename=filename,
        user_id=user_id,
        content_type=mime,
        bucket_name=bucket_name,
    )


def upload_avatar_to_supabase(
    base64_data: str,
    user_id: str,
    filename: str = "avatar.jpg",
) -> str:
    """Upload user avatar to the public avatars bucket and return permanent public URL."""
    clean_user_id = "".join(c for c in user_id if c.isalnum() or c in "-_")
    ext = os.path.splitext(filename)[1].lower() or ".jpg"
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        ext = ".jpg"
    storage_path = f"{clean_user_id}/avatar{ext}"

    if "," in base64_data:
        header, encoded = base64_data.split(",", 1)
        mime = header.split(";")[0].replace("data:", "") if "data:" in header else "image/jpeg"
    else:
        encoded = base64_data
        mime = "image/jpeg"

    try:
        file_bytes = base64.b64decode(encoded)
    except Exception as exc:
        raise ValueError("Invalid base64 string provided for avatar") from exc

    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY and not ("placeholder" in SUPABASE_URL):
        try:
            upload_url = f"{SUPABASE_URL}/storage/v1/object/avatars/{storage_path}"
            headers = _headers(mime)
            headers["x-upsert"] = "true"

            response = requests.post(
                upload_url,
                data=file_bytes,
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
            import time
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/avatars/{storage_path}?v={int(time.time())}"
            return public_url
        except Exception as e:
            print("[Storage] Supabase avatar upload failed, using data URL fallback:", e)

    # Fallback to data URL
    return f"data:{mime};base64,{encoded}"

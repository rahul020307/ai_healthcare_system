import json
import os
from functools import lru_cache
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database.sql_db import UserModel, get_db_session

router = APIRouter(prefix="/auth", tags=["Authentication"])
BEARER = HTTPBearer(auto_error=False)
SUPABASE_AUTH_ISSUER = os.getenv("SUPABASE_AUTH_ISSUER", "").rstrip("/")
SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL", "").strip()
SUPABASE_JWT_ALGORITHM = "ES256"
SUPABASE_JWT_AUDIENCE = "authenticated"


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    phone: str | None = None
    location: str | None = None
    age: int | None = None
    gender: str | None = None
    bloodGroup: str | None = None


def _require_supabase_auth_config() -> tuple[str, str]:
    if not SUPABASE_AUTH_ISSUER or not SUPABASE_JWKS_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication is not configured",
        )
    return SUPABASE_AUTH_ISSUER, SUPABASE_JWKS_URL


@lru_cache(maxsize=1)
def _load_supabase_jwks() -> dict[str, Any]:
    _, jwks_url = _require_supabase_auth_config()
    try:
        with urlopen(jwks_url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase signing keys are unavailable",
        ) from exc

    keys = payload.get("keys")
    if not isinstance(keys, list):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase signing keys response is invalid",
        )
    return payload


def _decode_supabase_access_token(token: str) -> dict[str, Any]:
    issuer, _ = _require_supabase_auth_config()
    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") != SUPABASE_JWT_ALGORITHM:
            raise JWTError("Unsupported signing algorithm")
        kid = header.get("kid")
        if not kid:
            raise JWTError("Missing signing key id")

        jwks = _load_supabase_jwks()
        matching_key = next(
            (
                key
                for key in jwks.get("keys", [])
                if isinstance(key, dict) and key.get("kid") == kid
            ),
            None,
        )
        if matching_key is None:
            raise JWTError("Unknown signing key id")

        return jwt.decode(
            token,
            matching_key,
            algorithms=[SUPABASE_JWT_ALGORITHM],
            audience=SUPABASE_JWT_AUDIENCE,
            issuer=issuer,
            options={"verify_aud": True, "verify_iss": True},
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(BEARER),
) -> UserModel:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    payload = _decode_supabase_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user id missing from access token",
        )

    session: Session = get_db_session()
    try:
        user = session.query(UserModel).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Application profile not found for authenticated user",
            )
        return user
    finally:
        session.close()


@router.get("/me", response_model=UserResponse)
def me(current_user: UserModel = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        phone=current_user.phone,
        location=current_user.location,
        age=current_user.age,
        gender=current_user.gender,
        bloodGroup=current_user.blood_group,
    )

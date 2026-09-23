from __future__ import annotations

import time
from typing import Any, Dict

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt

from app.core.config import settings

security = HTTPBearer(auto_error=False)
_JWKS_CACHE: dict[str, Any] = {"expires_at": 0.0, "keys": []}


def _supabase_url() -> str:
    return settings.SUPABASE_URL


def _jwks() -> list[dict[str, Any]]:
    now = time.time()
    if _JWKS_CACHE["keys"] and now < _JWKS_CACHE["expires_at"]:
        return _JWKS_CACHE["keys"]

    base_url = _supabase_url()
    if not base_url or "placeholder" in base_url:
        return []

    url = f"{base_url}/auth/v1/.well-known/jwks.json"
    try:
        response = requests.get(url, timeout=4)
        if response.status_code == 200:
            keys = response.json().get("keys", [])
            if keys:
                _JWKS_CACHE.update({"keys": keys, "expires_at": now + 300})
                return keys
    except Exception:
        pass
    return []


def get_current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> Dict[str, Any]:
    if credentials is None or not credentials.credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()
    supabase_base = _supabase_url()

    if supabase_base and not ("placeholder" in supabase_base or "curaassist-carehub.supabase.co" in supabase_base):
        try:
            keys = _jwks()
            if keys and "." in token:
                header = jwt.get_unverified_header(token)
                kid = header.get("kid")
                key = next((item for item in keys if item.get("kid") == kid), None)
                if key:
                    claims = jwt.decode(
                        token,
                        key,
                        algorithms=["ES256", "RS256", "HS256"],
                        audience="authenticated",
                        issuer=f"{supabase_base}/auth/v1",
                        options={"verify_exp": True},
                    )
                    subject = claims.get("sub")
                    email = claims.get("email")
                    if subject and email:
                        return {
                            "sub": subject,
                            "email": email,
                            "role": claims.get("role", "Patient"),
                            "claims": claims,
                        }
        except Exception:
            pass

    # No synthetic identity fallback is permitted for protected production APIs.
    # Local tests must pass an explicit identity object to get_current_user().
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(identity: Dict[str, Any] = Depends(get_current_identity)):
    """Resolve the verified Supabase Auth UUID to the application profile row."""
    from app.database.sql_db import UserModel, get_db_session

    user_id = identity.get("sub")
    email = identity.get("email")
    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user identity is incomplete",
        )

    session = get_db_session()
    try:
        user = session.query(UserModel).filter_by(auth_user_id=user_id).first()

        meta = identity.get("claims", {}).get("user_metadata", {}) or {}
        if not user:
            name_val = (
                meta.get("name")
                or identity.get("claims", {}).get("name")
                or email.split("@", 1)[0]
            )
            user = UserModel(
                # Keep the legacy ORM primary key string-compatible while making
                # Supabase Auth UUID authoritative for ownership.
                id=user_id,
                auth_user_id=user_id,
                name=name_val,
                email=email,
                phone=meta.get("phone") or "",
                blood_group=meta.get("blood") or meta.get("bloodGroup") or "O+",
                location=meta.get("city") or meta.get("location") or "Hyderabad, Telangana",
                age=int(meta.get("age", 30)) if str(meta.get("age", "")).isdigit() else 30,
                gender=meta.get("gender") or "Male",
                avatar_url=meta.get("avatar_url"),
                role="Patient",
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            # Do not rebind an existing profile to a different Auth UUID.
            if str(user.auth_user_id) != str(user_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Profile identity mismatch",
                )
            updated = False
            if meta.get("avatar_url") and user.avatar_url != meta["avatar_url"]:
                user.avatar_url = meta["avatar_url"]
                updated = True
            if meta.get("phone") and not user.phone:
                user.phone = meta["phone"]
                updated = True
            if updated:
                session.commit()
                session.refresh(user)

        session.expunge(user)
        return user
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to resolve authenticated application user",
        ) from exc
    finally:
        session.close()


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if not credentials or not credentials.credentials:
        return None
    try:
        identity = get_current_identity(credentials)
        return get_current_user(identity)
    except HTTPException:
        return None

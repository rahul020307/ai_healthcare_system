import os
import time
from typing import Any, Dict

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer(auto_error=False)
_JWKS_CACHE: dict[str, Any] = {"expires_at": 0.0, "keys": []}


def _supabase_url() -> str:
    value = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    if not value:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication is not configured",
        )
    return value


def _jwks() -> list[dict[str, Any]]:
    now = time.time()
    if _JWKS_CACHE["keys"] and now < _JWKS_CACHE["expires_at"]:
        return _JWKS_CACHE["keys"]

    url = f"{_supabase_url()}/auth/v1/.well-known/jwks.json"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        keys = response.json().get("keys", [])
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to load Supabase authentication keys",
        ) from exc

    if not keys:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication keys are unavailable",
        )

    _JWKS_CACHE.update({"keys": keys, "expires_at": now + 300})
    return keys


def get_current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> Dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    issuer = f"{_supabase_url()}/auth/v1"

    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        key = next((item for item in _jwks() if item.get("kid") == kid), None)
        if key is None:
            raise JWTError("Signing key not found")

        claims = jwt.decode(
            token,
            key,
            algorithms=["ES256"],
            audience="authenticated",
            issuer=issuer,
            options={"verify_exp": True},
        )
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Supabase access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = claims.get("sub")
    email = claims.get("email")
    if not subject or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated token is missing required identity claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "sub": subject,
        "email": email,
        "role": claims.get("role"),
        "claims": claims,
    }


def get_current_user(identity: Dict[str, Any] = Depends(get_current_identity)):
    """Resolve a verified Supabase identity to the application's SQL user row."""
    from app.database.sql_db import UserModel, get_db_session

    session = get_db_session()
    try:
        user = session.query(UserModel).filter_by(id=identity["sub"]).first()
        if not user:
            user = session.query(UserModel).filter_by(email=identity["email"]).first()

        if not user:
            user = UserModel(
                id=identity["sub"],
                name=identity["email"].split("@", 1)[0],
                email=identity["email"],
                role="Patient",
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        session.expunge(user)
        return user
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
    """Optionally resolves a verified Supabase user if Bearer token is provided, else returns None."""
    if not credentials or not credentials.credentials:
        return None
    try:
        identity = get_current_identity(credentials)
        return get_current_user(identity)
    except Exception:
        return None

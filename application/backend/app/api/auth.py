import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database.sql_db import UserModel, get_db_session

router = APIRouter(prefix="/auth", tags=["Authentication"])
BEARER = HTTPBearer(auto_error=False)
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
SUPABASE_JWT_ALGORITHM = os.getenv("SUPABASE_JWT_ALGORITHM", "HS256")


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


def _require_supabase_jwt_secret() -> str:
    if not SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication is not configured",
        )
    return SUPABASE_JWT_SECRET


def _decode_supabase_access_token(token: str) -> dict[str, Any]:
    secret = _require_supabase_jwt_secret()
    try:
        return jwt.decode(token, secret, algorithms=[SUPABASE_JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )


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
    if not user_id:
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

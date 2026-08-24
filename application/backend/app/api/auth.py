import hashlib
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field
from argon2 import PasswordHasher
from sqlalchemy.exc import IntegrityError

from app.database.sql_db import AuthSessionModel, UserModel, get_db_session

router = APIRouter(prefix="/auth", tags=["Authentication"])

PASSWORD_HASHER = PasswordHasher()
BEARER = HTTPBearer(auto_error=False)
JWT_SECRET = os.getenv("AUTH_JWT_SECRET")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 15
REFRESH_TOKEN_DAYS = 30

if not JWT_SECRET:
    JWT_SECRET = secrets.token_urlsafe(48)
    print("[Auth] AUTH_JWT_SECRET is not configured; using process-local secret. Configure it for production.")


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=512)


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


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    user: UserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str


def normalize_email(email: str) -> str:
    return email.strip().lower()


def user_to_response(user: UserModel) -> UserResponse:
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        phone=user.phone,
        location=user.location,
        age=user.age,
        gender=user.gender,
        bloodGroup=user.blood_group,
    )


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_refresh_session(user_id: str) -> tuple[str, AuthSessionModel]:
    raw_token = secrets.token_urlsafe(48)
    now = datetime.now(timezone.utc)
    session = AuthSessionModel(
        id=secrets.token_hex(16),
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=now + timedelta(days=REFRESH_TOKEN_DAYS),
        created_at=now,
    )
    return raw_token, session


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(BEARER),
) -> UserModel:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")

    user_id = payload.get("sub")
    if not user_id or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    session = get_db_session()
    try:
        user = session.query(UserModel).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    finally:
        session.close()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    email = normalize_email(str(payload.email))
    session = get_db_session()
    try:
        if session.query(UserModel).filter_by(email=email).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")

        user = UserModel(
            id=f"usr-{secrets.token_hex(10)}",
            name=payload.name.strip(),
            email=email,
            password_hash=PASSWORD_HASHER.hash(payload.password),
            role="Patient",
        )
        refresh_token, auth_session = issue_refresh_session(user.id)
        session.add(user)
        session.add(auth_session)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")

        return AuthResponse(
            access_token=create_access_token(user.id),
            refresh_token=refresh_token,
            user=user_to_response(user),
        )
    finally:
        session.close()


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    email = normalize_email(str(payload.email))
    session = get_db_session()
    try:
        user = session.query(UserModel).filter_by(email=email).first()
        if not user or not user.password_hash:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        try:
            PASSWORD_HASHER.verify(user.password_hash, payload.password)
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        refresh_token, auth_session = issue_refresh_session(user.id)
        session.add(auth_session)
        session.commit()
        return AuthResponse(
            access_token=create_access_token(user.id),
            refresh_token=refresh_token,
            user=user_to_response(user),
        )
    finally:
        session.close()


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest):
    token_hash = hash_refresh_token(payload.refresh_token)
    session = get_db_session()
    try:
        auth_session = session.query(AuthSessionModel).filter_by(token_hash=token_hash).first()
        now = datetime.now(timezone.utc)
        if not auth_session or auth_session.revoked_at is not None or auth_session.expires_at <= now:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

        user = session.query(UserModel).filter_by(id=auth_session.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        auth_session.revoked_at = now
        new_refresh_token, new_session = issue_refresh_session(user.id)
        session.add(new_session)
        session.commit()
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=new_refresh_token,
        )
    finally:
        session.close()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest):
    token_hash = hash_refresh_token(payload.refresh_token)
    session = get_db_session()
    try:
        auth_session = session.query(AuthSessionModel).filter_by(token_hash=token_hash).first()
        if auth_session and auth_session.revoked_at is None:
            auth_session.revoked_at = datetime.now(timezone.utc)
            session.commit()
    finally:
        session.close()


@router.get("/me", response_model=UserResponse)
def me(current_user: UserModel = Depends(get_current_user)):
    return user_to_response(current_user)

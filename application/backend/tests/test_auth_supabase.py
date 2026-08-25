import os

import pytest
from fastapi import HTTPException

os.environ["SUPABASE_JWT_SECRET"] = "test-supabase-jwt-secret"

from app.api.auth import create_test_supabase_token, get_current_user  # noqa: E402


class DummyCredentials:
    scheme = "Bearer"

    def __init__(self, credentials: str):
        self.credentials = credentials


def test_valid_supabase_token(monkeypatch):
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    token = create_test_supabase_token(user_id)
    user = get_current_user(DummyCredentials(token))
    assert user.id == user_id


def test_invalid_signature_rejected(monkeypatch):
    token = create_test_supabase_token("550e8400-e29b-41d4-a716-446655440000", secret="wrong-secret")
    with pytest.raises(HTTPException) as exc:
        get_current_user(DummyCredentials(token))
    assert exc.value.status_code == 401


def test_expired_token_rejected():
    token = create_test_supabase_token(
        "550e8400-e29b-41d4-a716-446655440000",
        expires_in=-60,
    )
    with pytest.raises(HTTPException) as exc:
        get_current_user(DummyCredentials(token))
    assert exc.value.status_code == 401


def test_missing_token_rejected():
    with pytest.raises(HTTPException) as exc:
        get_current_user(None)
    assert exc.value.status_code == 401


def test_missing_sub_rejected():
    token = create_test_supabase_token(None)
    with pytest.raises(HTTPException) as exc:
        get_current_user(DummyCredentials(token))
    assert exc.value.status_code == 401


def test_current_user_comes_from_token_sub():
    user_id = "550e8400-e29b-41d4-a716-446655440001"
    token = create_test_supabase_token(user_id)
    user = get_current_user(DummyCredentials(token))
    assert user.id == user_id

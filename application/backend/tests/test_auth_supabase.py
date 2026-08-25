import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from jose import jwt

os.environ["SUPABASE_JWT_SECRET"] = "test-supabase-jwt-secret"
os.environ["SUPABASE_JWT_ALGORITHM"] = "HS256"

from app.api.auth import _decode_supabase_access_token, get_current_user  # noqa: E402


TEST_SECRET = "test-supabase-jwt-secret"
TEST_ALGORITHM = "HS256"
USER_ID = "550e8400-e29b-41d4-a716-446655440000"


class DummyCredentials:
    scheme = "Bearer"

    def __init__(self, credentials: str):
        self.credentials = credentials


def make_token(*, sub=USER_ID, secret=TEST_SECRET, expires_at=None, extra=None):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((expires_at or (now + timedelta(minutes=5))).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, secret, algorithm=TEST_ALGORITHM)


def test_valid_supabase_token_decodes():
    token = make_token()
    payload = _decode_supabase_access_token(token)
    assert payload["sub"] == USER_ID


def test_invalid_signature_rejected():
    token = make_token(secret="wrong-secret")
    with pytest.raises(HTTPException) as exc:
        _decode_supabase_access_token(token)
    assert exc.value.status_code == 401


def test_expired_token_rejected():
    token = make_token(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    with pytest.raises(HTTPException) as exc:
        _decode_supabase_access_token(token)
    assert exc.value.status_code == 401


def test_missing_authorization_header_rejected():
    with pytest.raises(HTTPException) as exc:
        get_current_user(None)
    assert exc.value.status_code == 401


def test_malformed_bearer_header_rejected():
    credentials = DummyCredentials("not-a-jwt")
    with pytest.raises(HTTPException) as exc:
        get_current_user(credentials)
    assert exc.value.status_code == 401


def test_missing_sub_claim_rejected():
    token = make_token(sub=None)
    with pytest.raises(HTTPException) as exc:
        get_current_user(DummyCredentials(token))
    assert exc.value.status_code == 401


def test_invalid_or_missing_sub_value_rejected():
    token = make_token(extra={"sub": ""})
    with pytest.raises(HTTPException) as exc:
        get_current_user(DummyCredentials(token))
    assert exc.value.status_code == 401


def test_current_user_is_resolved_from_token_sub():
    user = type("User", (), {"id": USER_ID})()
    token = make_token()
    with patch("app.api.auth.get_db_session") as get_db_session:
        session = get_db_session.return_value
        session.query.return_value.filter_by.return_value.first.return_value = user
        resolved = get_current_user(DummyCredentials(token))
    assert resolved.id == USER_ID


def test_nonexistent_sub_user_rejected():
    token = make_token()
    with patch("app.api.auth.get_db_session") as get_db_session:
        session = get_db_session.return_value
        session.query.return_value.filter_by.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc:
            get_current_user(DummyCredentials(token))
    assert exc.value.status_code == 401


def test_missing_supabase_secret_fails_closed():
    token = make_token()
    with patch("app.api.auth.SUPABASE_JWT_SECRET", None):
        with pytest.raises(HTTPException) as exc:
            _decode_supabase_access_token(token)
    assert exc.value.status_code == 503

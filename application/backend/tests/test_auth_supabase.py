import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi import HTTPException
from jose import jwt

TEST_ISSUER = "https://example.supabase.co/auth/v1"
TEST_JWKS_URL = "https://example.supabase.co/auth/v1/.well-known/jwks.json"
TEST_AUDIENCE = "authenticated"
TEST_KID = "test-kid"
USER_ID = "550e8400-e29b-41d4-a716-446655440000"


class DummyCredentials:
    scheme = "Bearer"

    def __init__(self, credentials: str):
        self.credentials = credentials


def _jwk_from_public_key(public_key, kid=TEST_KID):
    numbers = public_key.public_numbers()
    x = numbers.x.to_bytes(32, "big")
    y = numbers.y.to_bytes(32, "big")
    def b64url(value: bytes) -> str:
        import base64
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")
    return {
        "kty": "EC",
        "crv": "P-256",
        "x": b64url(x),
        "y": b64url(y),
        "alg": "ES256",
        "use": "sig",
        "kid": kid,
    }


@pytest.fixture()
def auth_test_setup(monkeypatch):
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    jwk = _jwk_from_public_key(public_key)
    jwks = {"keys": [jwk]}
    monkeypatch.setattr("app.api.auth.SUPABASE_AUTH_ISSUER", TEST_ISSUER)
    monkeypatch.setattr("app.api.auth.SUPABASE_JWKS_URL", TEST_JWKS_URL)
    app_auth = __import__("app.api.auth", fromlist=["_load_supabase_jwks"])
    app_auth._load_supabase_jwks.cache_clear()
    monkeypatch.setattr(app_auth, "_load_supabase_jwks", lambda: jwks)
    return private_key


def make_token(private_key, *, sub=USER_ID, kid=TEST_KID, issuer=TEST_ISSUER, audience=TEST_AUDIENCE,
               algorithm="ES256", expires_at=None, extra=None):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((expires_at or (now + timedelta(minutes=5))).timestamp()),
        "iss": issuer,
        "aud": audience,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(
        payload,
        private_key,
        algorithm=algorithm,
        headers={"kid": kid},
    )


def test_valid_es256_token_and_matching_kid(auth_test_setup):
    from app.api.auth import _decode_supabase_access_token
    token = make_token(auth_test_setup)
    payload = _decode_supabase_access_token(token)
    assert payload["sub"] == USER_ID


def test_invalid_signature_rejected(auth_test_setup):
    from app.api.auth import _decode_supabase_access_token
    wrong_key = ec.generate_private_key(ec.SECP256R1())
    token = make_token(wrong_key)
    with pytest.raises(HTTPException) as exc:
        _decode_supabase_access_token(token)
    assert exc.value.status_code == 401


def test_unknown_kid_rejected(auth_test_setup):
    from app.api.auth import _decode_supabase_access_token
    token = make_token(auth_test_setup, kid="unknown-kid")
    with pytest.raises(HTTPException) as exc:
        _decode_supabase_access_token(token)
    assert exc.value.status_code == 401


def test_expired_token_rejected(auth_test_setup):
    from app.api.auth import _decode_supabase_access_token
    token = make_token(auth_test_setup, expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    with pytest.raises(HTTPException) as exc:
        _decode_supabase_access_token(token)
    assert exc.value.status_code == 401


def test_wrong_issuer_rejected(auth_test_setup):
    from app.api.auth import _decode_supabase_access_token
    token = make_token(auth_test_setup, issuer="https://wrong.example/auth/v1")
    with pytest.raises(HTTPException) as exc:
        _decode_supabase_access_token(token)
    assert exc.value.status_code == 401


def test_wrong_audience_rejected(auth_test_setup):
    from app.api.auth import _decode_supabase_access_token
    token = make_token(auth_test_setup, audience="anon")
    with pytest.raises(HTTPException) as exc:
        _decode_supabase_access_token(token)
    assert exc.value.status_code == 401


def test_wrong_algorithm_rejected(auth_test_setup):
    from app.api.auth import _decode_supabase_access_token
    token = jwt.encode(
        {"sub": USER_ID, "iss": TEST_ISSUER, "aud": TEST_AUDIENCE,
         "iat": int(datetime.now(timezone.utc).timestamp()),
         "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp())},
        auth_test_setup,
        algorithm="ES256",
        headers={"kid": TEST_KID, "alg": "HS256"},
    )
    with pytest.raises(HTTPException) as exc:
        _decode_supabase_access_token(token)
    assert exc.value.status_code == 401


def test_missing_sub_rejected(auth_test_setup):
    from app.api.auth import _decode_supabase_access_token
    token = make_token(auth_test_setup, sub=None)
    with pytest.raises(HTTPException) as exc:
        _decode_supabase_access_token(token)
    assert exc.value.status_code == 401


def test_missing_or_malformed_bearer_rejected():
    from app.api.auth import get_current_user
    with pytest.raises(HTTPException) as exc:
        get_current_user(None)
    assert exc.value.status_code == 401
    with pytest.raises(HTTPException) as exc:
        get_current_user(DummyCredentials("not-a-jwt"))
    assert exc.value.status_code == 401


def test_valid_sub_resolves_to_user(auth_test_setup):
    from app.api.auth import get_current_user
    token = make_token(auth_test_setup)
    user = type("User", (), {"id": USER_ID})()
    with patch("app.api.auth.get_db_session") as get_db_session:
        session = get_db_session.return_value
        session.query.return_value.filter_by.return_value.first.return_value = user
        resolved = get_current_user(DummyCredentials(token))
    assert resolved.id == USER_ID


def test_nonexistent_user_rejected(auth_test_setup):
    from app.api.auth import get_current_user
    token = make_token(auth_test_setup)
    with patch("app.api.auth.get_db_session") as get_db_session:
        session = get_db_session.return_value
        session.query.return_value.filter_by.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc:
            get_current_user(DummyCredentials(token))
    assert exc.value.status_code == 401


def test_jwks_unavailable_fails_closed(monkeypatch, auth_test_setup):
    from app.api.auth import _decode_supabase_access_token
    token = make_token(auth_test_setup)
    def fail_jwks():
        raise HTTPException(status_code=503, detail="Supabase signing keys are unavailable")
    monkeypatch.setattr("app.api.auth._load_supabase_jwks", fail_jwks)
    with pytest.raises(HTTPException) as exc:
        _decode_supabase_access_token(token)
    assert exc.value.status_code == 503

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import get_current_identity


def test_missing_bearer_token_is_rejected():
    with pytest.raises(HTTPException) as exc:
        get_current_identity(None)

    assert exc.value.status_code == 401
    assert exc.value.headers["WWW-Authenticate"] == "Bearer"


def test_non_bearer_scheme_is_rejected():
    credentials = HTTPAuthorizationCredentials(
        scheme="Basic",
        credentials="not-a-jwt",
    )

    with pytest.raises(HTTPException) as exc:
        get_current_identity(credentials)

    assert exc.value.status_code == 401

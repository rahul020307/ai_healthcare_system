from app.core.config import settings
from app.database.astra import get_astra_database, is_astra_configured


def test_astra_requires_runtime_credentials(monkeypatch):
    monkeypatch.setattr(settings, "ASTRA_DB_API_ENDPOINT", "")
    monkeypatch.setattr(settings, "ASTRA_DB_APPLICATION_TOKEN", "")

    assert is_astra_configured() is False

    try:
        get_astra_database()
    except RuntimeError as exc:
        assert "ASTRA_DB_API_ENDPOINT" in str(exc)
    else:
        raise AssertionError("Astra connection should require runtime credentials")

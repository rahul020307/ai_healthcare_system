"""Astra DB Data API integration for CuraAssist CareHub.

This module provides a lazy, backend-only connection to Astra DB Serverless.
Credentials are read exclusively from deployment environment variables.
"""

from __future__ import annotations

from typing import Any

from astrapy import DataAPIClient

from app.core.config import settings


_client: DataAPIClient | None = None
_database: Any | None = None


def is_astra_configured() -> bool:
    """Return True when both required Astra credentials are configured."""
    return bool(
        settings.ASTRA_DB_API_ENDPOINT
        and settings.ASTRA_DB_APPLICATION_TOKEN
    )


def get_astra_database() -> Any:
    """Return the configured Astra DB database object.

    The client and database are initialized lazily so local development and
    unrelated application startup paths do not require Astra credentials.
    """
    global _client, _database

    if not is_astra_configured():
        raise RuntimeError(
            "ASTRA_DB_API_ENDPOINT and ASTRA_DB_APPLICATION_TOKEN are required"
        )

    if _database is None:
        if _client is None:
            _client = DataAPIClient()
        _database = _client.get_database(
            settings.ASTRA_DB_API_ENDPOINT,
            token=settings.ASTRA_DB_APPLICATION_TOKEN,
            keyspace=settings.ASTRA_DB_KEYSPACE,
        )

    return _database


def get_astra_collection(collection_name: str) -> Any:
    """Return a collection from the configured Astra working keyspace."""
    if not collection_name.strip():
        raise ValueError("Astra collection name cannot be empty")
    return get_astra_database().get_collection(collection_name.strip())


def check_astra_connection() -> dict[str, Any]:
    """Perform a lightweight authenticated Astra DB connectivity check."""
    if not is_astra_configured():
        return {
            "status": "not_configured",
            "configured": False,
            "keyspace": settings.ASTRA_DB_KEYSPACE,
        }

    try:
        database = get_astra_database()
        collections = database.list_collection_names()
        return {
            "status": "online",
            "configured": True,
            "keyspace": settings.ASTRA_DB_KEYSPACE,
            "collection_count": len(collections),
            "collections": collections,
        }
    except Exception as exc:
        return {
            "status": "error",
            "configured": True,
            "keyspace": settings.ASTRA_DB_KEYSPACE,
            "error": str(exc),
        }

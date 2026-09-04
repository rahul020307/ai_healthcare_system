"""
Authentication module backward compatibility wrapper.
Core authentication security is implemented in app.core.security.
"""
from app.core.security import (
    security,
    _supabase_url,
    _jwks,
    get_current_identity,
    get_current_user,
    get_optional_current_user,
)

__all__ = [
    "security",
    "_supabase_url",
    "_jwks",
    "get_current_identity",
    "get_current_user",
    "get_optional_current_user",
]

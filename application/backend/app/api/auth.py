from fastapi import APIRouter, Depends

from app.auth import get_current_identity

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me")
def get_authenticated_identity(identity: dict = Depends(get_current_identity)):
    return {
        "status": "success",
        "authenticated": True,
        "user": {
            "id": identity["sub"],
            "email": identity["email"],
            "role": identity.get("role"),
        },
    }

from fastapi import APIRouter

router = APIRouter(prefix="/home", tags=["Home"])


@router.get("/")
def get_home():
    return {
        "welcome": "Welcome to SmartCare",
        "health_tip": "Drink plenty of water today.",
        "quick_actions": [
            "AI Assistant",
            "Medicine Scanner",
            "Prescription Scanner",
            "Emergency"
        ]
    }
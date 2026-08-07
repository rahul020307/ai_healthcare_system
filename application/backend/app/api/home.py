from fastapi import APIRouter

router = APIRouter(prefix="/home", tags=["Home"])


@router.get("/")
def get_home_dashboard():
    return {
        "status": "success",
        "welcome": "Welcome back to CuraAssist CareHub",
        "health_tip": "Stay hydrated! Drink 8 glasses of water daily and take 10-minute walks between long work sessions.",
        "quick_actions": [
            {"id": "scan-med", "name": "Scan Medicine", "icon": "camera", "color": "teal"},
            {"id": "upload-rx", "name": "Upload Rx", "icon": "file-text", "color": "rose"},
            {"id": "ask-ai", "name": "Ask AI Bot", "icon": "bot", "color": "cyan"},
            {"id": "reminders", "name": "Schedule", "icon": "clock", "color": "amber"}
        ],
        "popular_categories": [
            {"name": "Prescription Care", "itemCount": 42},
            {"name": "Vitamins & Supplements", "itemCount": 85},
            {"name": "Pain Relief", "itemCount": 34},
            {"name": "First Aid & Bandages", "itemCount": 19}
        ]
    }


@router.get("/health-tips")
def get_health_tips():
    return [
        {"id": 1, "title": "Hydration Reminder", "desc": "Drinking water boosts energy and supports renal function."},
        {"id": 2, "title": "Regular BP Checks", "desc": "Monitor blood pressure weekly for proactive cardiac health."},
        {"id": 3, "title": "Post-Meal Walks", "desc": "A 10-minute walk post-dinner stabilizes blood sugar levels."}
    ]


@router.get("/db-status")
def get_database_status():
    from app.database.mongodb import check_mongodb_connection
    return {
        "status": "success",
        "database": check_mongodb_connection()
    }
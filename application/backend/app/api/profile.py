from fastapi import APIRouter

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/user")
def get_user_profile():
    return {
        "status": "success",
        "user": {
            "name": "Rahul Sharma",
            "verified": True,
            "phone": "+91 98765 43210",
            "email": "rahul.sharma@email.com",
            "location": "Hyderabad, Telangana",
            "age": 34,
            "gender": "Male",
            "bloodGroup": "O+",
            "familyMembers": [
                {"id": "fam1", "name": "Rahul Sharma", "relation": "Self"},
                {"id": "fam2", "name": "Eleanor Sharma", "relation": "Mother"},
                {"id": "fam3", "name": "Sarah Sharma", "relation": "Wife"},
                {"id": "fam4", "name": "Leo Sharma", "relation": "Son"}
            ]
        },
        "healthRecords": [
            {"title": "Medical Reports", "desc": "X-Rays, Blood Tests, Lab Reports"},
            {"title": "Immunization", "desc": "COVID Booster (Nov 2025), Flu Spikevax"},
            {"title": "Vitals History", "desc": "BP 120/80 mmHg, Sugar 95 mg/dL, BMI 22.4"}
        ]
    }

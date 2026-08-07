from fastapi import APIRouter
from typing import Optional
import math

router = APIRouter(prefix="/maps", tags=["Maps"])


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@router.get("/facilities")
def get_nearby_facilities(lat: Optional[float] = 17.3850, lng: Optional[float] = 78.4867, category: Optional[str] = "all"):
    base_facilities = [
        {
            "id": "f1",
            "name": "Apollo City Hospital & Trauma Center",
            "type": "Hospitals",
            "rating": 4.9,
            "reviews": 1280,
            "address": "Road No. 1, Jubilee Hills",
            "phone": "+91 40 2360 7777",
            "openNow": True,
            "lat": lat + 0.003,
            "lng": lng + 0.002,
            "bedsAvailable": 14,
            "icuStatus": "Available"
        },
        {
            "id": "f2",
            "name": "MedPlus 24x7 Express Pharmacy",
            "type": "Pharmacies",
            "rating": 4.8,
            "reviews": 640,
            "address": "Cyber Towers Main Gate",
            "phone": "+91 40 4455 6677",
            "openNow": True,
            "lat": lat - 0.004,
            "lng": lng - 0.003,
            "homeDelivery": True
        },
        {
            "id": "f3",
            "name": "Vijaya Diagnostic & Pathology Lab",
            "type": "Labs",
            "rating": 4.7,
            "reviews": 410,
            "address": "Hitech City Metro Pillar 24",
            "phone": "+91 40 2233 4455",
            "openNow": True,
            "lat": lat + 0.006,
            "lng": lng - 0.005,
            "accredited": "NABL Certified"
        },
        {
            "id": "f4",
            "name": "Red Cross Emergency Blood Bank",
            "type": "Emergency",
            "rating": 4.9,
            "reviews": 890,
            "address": "Central Medical Square",
            "phone": "108",
            "openNow": True,
            "lat": lat - 0.002,
            "lng": lng + 0.007,
            "bloodTypesAvailable": ["O+", "A+", "B+", "AB+", "O-"]
        }
    ]

    for f in base_facilities:
        dist = haversine_distance(lat, lng, f["lat"], f["lng"])
        f["distanceKm"] = round(dist, 2)
        f["distanceText"] = f"{round(dist, 1)} km"

    base_facilities.sort(key=lambda x: x["distanceKm"])

    if category and category != "all":
        base_facilities = [f for f in base_facilities if f["type"].lower() == category.lower()]

    return {
        "status": "success",
        "userLocation": {"lat": lat, "lng": lng},
        "count": len(base_facilities),
        "facilities": base_facilities
    }

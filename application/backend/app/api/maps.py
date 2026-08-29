import math
from typing import Optional
from fastapi import APIRouter

from app.database.sql_db import get_db_session, FacilityModel

router = APIRouter(prefix="/maps", tags=["Maps"])


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.get("/facilities")
def get_nearby_facilities(
    lat: Optional[float] = 17.3850,
    lng: Optional[float] = 78.4867,
    category: Optional[str] = "all",
):
    """
    Return only facilities that actually exist in the application's facility database.

    Coordinates are used only to calculate distance. No synthetic hospitals,
    pharmacies, laboratories, clinics, or blood banks are generated at runtime.
    """
    user_lat = lat if lat is not None else 17.3850
    user_lng = lng if lng is not None else 78.4867

    session = get_db_session()
    try:
        db_facilities = session.query(FacilityModel).all()
        facilities = []
        for facility in db_facilities:
            distance_km = haversine_distance(user_lat, user_lng, facility.lat, facility.lng)
            facilities.append({
                "id": facility.id,
                "name": facility.name,
                "type": facility.type,
                "address": facility.address,
                "phone": facility.phone,
                "lat": facility.lat,
                "lng": facility.lng,
                "rating": facility.rating,
                "openHours": facility.open_hours,
                "is24x7": "24" in (facility.open_hours or "") or bool(facility.emergency_available),
                "emergencyAvailable": bool(facility.emergency_available),
                "distanceKm": round(distance_km, 2),
                "distanceText": f"{round(distance_km, 1)} km",
                "etaMins": max(2, int(distance_km * 2.5)),
                "dataSource": "application facility database",
                "liveVerified": False,
            })
    except Exception as exc:
        print("[Maps API] SQL Query error:", exc)
        raise
    finally:
        session.close()

    # Never invent healthcare providers when the database has insufficient data.
    facilities = [facility for facility in facilities if facility["distanceKm"] <= 35.0]
    cat_lower = (category or "all").lower().strip()
    if cat_lower and cat_lower != "all":
        facilities = [
            facility for facility in facilities
            if facility["type"].lower() == cat_lower
            or (cat_lower in {"emergency", "blood banks"} and facility["type"].lower() in {"emergency", "blood banks"})
        ]

    facilities.sort(key=lambda facility: facility["distanceKm"])

    return {
        "status": "success",
        "source": "Application Facility Database + Haversine Distance",
        "userLocation": {"lat": user_lat, "lng": user_lng},
        "count": len(facilities),
        "facilities": facilities,
        "liveAvailabilityVerified": False,
    }

import json
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/store", tags=["Store"])

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "medicines.json")

def load_json_medicines():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading medicines.json:", e)
    return []


class OrderItem(BaseModel):
    id: str
    name: str
    price: float
    quantity: int


class OrderRequest(BaseModel):
    userId: str
    items: List[OrderItem]
    totalAmount: float
    address: str
    paymentMethod: str


@router.get("/medicines")
def get_medicines(
    category: Optional[str] = "all",
    search: Optional[str] = "",
    location: Optional[str] = "Hyderabad, Telangana",
    lat: Optional[float] = 17.3850,
    lng: Optional[float] = 78.4867
):
    loc_lower = (location or "").lower()

    # Determine region & fulfillment hub based on location
    if "london" in loc_lower or "uk" in loc_lower or "united kingdom" in loc_lower:
        currency = "£"
        rate = 0.0095
        hub = "Boots Chemist • London Central Hub"
        eta = "20-30 mins"
    elif "new york" in loc_lower or "us" in loc_lower or "usa" in loc_lower:
        currency = "$"
        rate = 0.012
        hub = "CVS Pharmacy • Manhattan Center"
        eta = "15-25 mins"
    elif "mumbai" in loc_lower:
        currency = "₹"
        rate = 1.0
        hub = "Apollo Pharmacy • Bandra West"
        eta = "18-28 mins"
    elif "delhi" in loc_lower or "new delhi" in loc_lower:
        currency = "₹"
        rate = 1.0
        hub = "Max Health Pharmacy • Connaught Place"
        eta = "20-35 mins"
    elif "bengaluru" in loc_lower or "bangalore" in loc_lower:
        currency = "₹"
        rate = 1.0
        hub = "MedPlus Express • Indiranagar"
        eta = "15-20 mins"
    else:
        currency = "₹"
        rate = 1.0
        hub = f"MedPlus Express • {location or 'Local City Center'}"
        eta = "15-30 mins"

    json_records = load_json_medicines()

    base_medicines = []
    for item in json_records:
        raw_price = item.get("price", 50.0)
        orig_price = round(raw_price * 1.25, 2)
        base_medicines.append({
            "id": item.get("medicine_id", "med-1"),
            "name": item.get("brand_name", item.get("generic_name", "Medicine")),
            "genericName": item.get("generic_name", ""),
            "composition": item.get("composition", ""),
            "category": item.get("category", "General"),
            "price": round(raw_price * rate, 2),
            "originalPrice": round(orig_price * rate, 2),
            "currency": currency,
            "discount": "20% OFF",
            "rating": 4.8,
            "reviews": 120,
            "dosage": item.get("dosage", "1 tablet post meal"),
            "image": item.get("image_url", "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=300"),
            "genericAlt": f"{item.get('generic_name', 'Generic')} ({currency}{round(raw_price * 0.4 * rate, 2)})",
            "requiresRx": item.get("prescription_required", False),
            "fulfillingStore": hub,
            "deliveryEta": eta,
            "stockStatus": "In Stock (Available Nearby)"
        })

    cat_lower = (category or "all").lower()
    search_lower = (search or "").lower()

    results = []
    for m in base_medicines:
        cat_match = cat_lower == "all" or cat_lower in m["category"].lower() or m["category"].lower() in cat_lower
        name_match = not search_lower or search_lower in m["name"].lower() or search_lower in m["genericName"].lower() or search_lower in m["category"].lower()
        if cat_match and name_match:
            results.append(m)

    return {
        "status": "success",
        "activeLocation": location,
        "fulfillingStore": hub,
        "deliveryEta": eta,
        "count": len(results),
        "medicines": results
    }


@router.post("/orders")
def place_order(order: OrderRequest):
    if not order.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    return {
        "status": "success",
        "orderId": "ORD-982415",
        "message": f"Order placed successfully! Delivery scheduled to {order.address} within 25-30 mins.",
        "summary": {
            "totalAmount": order.totalAmount,
            "itemCount": len(order.items),
            "deliveryAddress": order.address,
            "paymentMethod": order.paymentMethod
        }
    }

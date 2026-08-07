from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/store", tags=["Store"])


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

    base_medicines = [
        {
            "id": "m1",
            "name": "Paracetamol 650mg Tablet",
            "category": "Pain Relief",
            "price": round(32.50 * rate, 2),
            "originalPrice": round(45.00 * rate, 2),
            "currency": currency,
            "discount": "28% OFF",
            "rating": 4.8,
            "reviews": 342,
            "dosage": "1 tablet every 6 hours post meals",
            "image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=300",
            "genericAlt": f"Acetaminophen 650mg ({currency}{round(18.00 * rate, 2)})",
            "requiresRx": False,
            "fulfillingStore": hub,
            "deliveryEta": eta,
            "stockStatus": "In Stock (High Availability)"
        },
        {
            "id": "m2",
            "name": "Vitamin C 500mg (Zinc + D3)",
            "category": "Supplements",
            "price": round(140.00 * rate, 2),
            "originalPrice": round(175.00 * rate, 2),
            "currency": currency,
            "discount": "20% OFF",
            "rating": 4.9,
            "reviews": 512,
            "dosage": "1 chewable tablet daily",
            "image": "https://images.unsplash.com/photo-1577401239170-897942555fb3?auto=format&fit=crop&q=80&w=300",
            "genericAlt": f"Ascorbic Acid 500mg ({currency}{round(75.00 * rate, 2)})",
            "requiresRx": False,
            "fulfillingStore": hub,
            "deliveryEta": eta,
            "stockStatus": "In Stock (18 units nearby)"
        },
        {
            "id": "m3",
            "name": "Dolo 650mg Fever & Pain Relief",
            "category": "Pain Relief",
            "price": round(30.00 * rate, 2),
            "originalPrice": round(38.00 * rate, 2),
            "currency": currency,
            "discount": "21% OFF",
            "rating": 4.7,
            "reviews": 890,
            "dosage": "1 tablet as prescribed by physician",
            "image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=300",
            "genericAlt": f"Paracetamol 650mg Generic ({currency}{round(15.00 * rate, 2)})",
            "requiresRx": False,
            "fulfillingStore": hub,
            "deliveryEta": eta,
            "stockStatus": "Fast 15-min Express Delivery"
        },
        {
            "id": "m4",
            "name": "Amoxicillin 500mg Antibiotic Capsule",
            "category": "Antibiotics",
            "price": round(88.00 * rate, 2),
            "originalPrice": round(110.00 * rate, 2),
            "currency": currency,
            "discount": "20% OFF",
            "rating": 4.6,
            "reviews": 128,
            "dosage": "1 capsule twice daily for 5 days",
            "image": "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?auto=format&fit=crop&q=80&w=300",
            "genericAlt": f"Amox 500 Generic ({currency}{round(42.00 * rate, 2)})",
            "requiresRx": True,
            "fulfillingStore": hub,
            "deliveryEta": eta,
            "stockStatus": "Prescription Verification Required"
        },
        {
            "id": "m5",
            "name": "Lipitor (Atorvastatin 10mg)",
            "category": "Cholesterol",
            "price": round(210.00 * rate, 2),
            "originalPrice": round(250.00 * rate, 2),
            "currency": currency,
            "discount": "16% OFF",
            "rating": 4.8,
            "reviews": 210,
            "dosage": "1 tablet daily at bedtime",
            "image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=300",
            "genericAlt": f"Atorvastatin 10mg ({currency}{round(95.00 * rate, 2)})",
            "requiresRx": True,
            "fulfillingStore": hub,
            "deliveryEta": eta,
            "stockStatus": "In Stock (Verified Pharmacy Hub)"
        }
    ]

    if category and category != "all":
        base_medicines = [m for m in base_medicines if m["category"].lower() == category.lower()]

    if search:
        s = search.lower()
        base_medicines = [m for m in base_medicines if s in m["name"].lower() or s in m["category"].lower()]

    return {
        "status": "success",
        "activeLocation": location,
        "fulfillingStore": hub,
        "deliveryEta": eta,
        "count": len(base_medicines),
        "medicines": base_medicines
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

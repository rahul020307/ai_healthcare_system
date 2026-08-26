import json
import os
import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.database.sql_db import get_db_session, OrderModel, UserModel

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
    userId: Optional[str] = None
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
    lng: Optional[float] = 78.4867,
):
    loc_lower = (location or "").lower()
    if "mumbai" in loc_lower:
        currency, rate, hub, eta = "₹", 1.0, "Apollo Pharmacy • Bandra West", "18-28 mins"
    elif "delhi" in loc_lower or "new delhi" in loc_lower:
        currency, rate, hub, eta = "₹", 1.0, "Max Health Pharmacy • Connaught Place", "20-35 mins"
    elif "bengaluru" in loc_lower or "bangalore" in loc_lower:
        currency, rate, hub, eta = "₹", 1.0, "MedPlus Express • Indiranagar", "15-20 mins"
    elif "hyderabad" in loc_lower:
        currency, rate, hub, eta = "₹", 1.0, "Apollo Pharmacy • Banjara Hills", "15-25 mins"
    else:
        currency, rate, hub, eta = "₹", 1.0, f"MedPlus Express • {location or 'Indian City Center'}", "15-30 mins"

    json_records = load_json_medicines()
    base_medicines = []
    for item in json_records:
        raw_price = item.get("price", 50.0)
        orig_price = item.get("original_price", round(raw_price * 1.25, 2))
        base_medicines.append({
            "id": item.get("medicine_id", "med-1"),
            "name": item.get("brand_name", item.get("generic_name", "Medicine")),
            "genericName": item.get("generic_name", ""),
            "composition": item.get("composition", ""),
            "category": item.get("category", "General"),
            "price": round(raw_price * rate, 2),
            "originalPrice": round(orig_price * rate, 2),
            "currency": currency,
            "discount": f"{round((1 - raw_price/orig_price)*100)}% OFF" if orig_price > raw_price else "Best Price",
            "rating": item.get("rating", 4.8),
            "reviews": item.get("reviews_count", 120),
            "dosage": item.get("dosage", "1 tablet post meal"),
            "image": item.get("image_url", "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=300"),
            "genericAlt": f"{item.get('generic_name', 'Generic')} ({currency}{round(raw_price * 0.4 * rate, 2)})",
            "requiresRx": item.get("prescription_required", False),
            "fulfillingStore": hub,
            "deliveryEta": eta,
            "stockStatus": "In Stock (Available Nearby)",
            "manufacturer": item.get("manufacturer", "Pharma Certified"),
            "platformSources": item.get("platform_sources", ["Tata 1mg", "Apollo Pharmacy", "Netmeds", "PharmEasy"]),
            "verifiedPlatforms": item.get("verified_platforms", ["Tata 1mg Verified", "Apollo Certified"]),
            "uses": item.get("uses", []),
            "sideEffects": item.get("side_effects", []),
            "warnings": item.get("warnings", []),
            "contraindications": item.get("contraindications", []),
            "storage": item.get("storage", "Store in a cool dry place."),
            "barcode": item.get("barcode", "8901234567890"),
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
        "medicines": results,
    }


@router.get("/orders")
def get_user_orders(email: Optional[str] = "rahul.sharma@email.com"):
    session = get_db_session()
    try:
        user = session.query(UserModel).filter_by(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found")
        orders = (
            session.query(OrderModel)
            .filter(OrderModel.owner_user_id == user.id)
            .order_by(OrderModel.created_at.desc())
            .all()
        )
        res = []
        for o in orders:
            try:
                items_data = json.loads(o.items_json)
            except Exception:
                items_data = []
            res.append({
                "orderId": o.id,
                "userEmail": o.user_email,
                "patientName": o.patient_name,
                "items": items_data,
                "totalAmount": o.total_amount,
                "address": o.delivery_address,
                "paymentMethod": o.payment_method,
                "status": o.status,
                "createdAt": o.created_at.isoformat() if o.created_at else datetime.datetime.utcnow().isoformat(),
            })
        return {"status": "success", "source": "SQL Database", "count": len(res), "orders": res}
    finally:
        session.close()


@router.post("/orders")
def place_order(order: OrderRequest):
    if not order.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    session = get_db_session()
    try:
        email = order.userId or "rahul.sharma@email.com"
        user = session.query(UserModel).filter_by(email=email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found")

        order_id = f"ORD-{int(datetime.datetime.utcnow().timestamp() * 1000) % 1000000:06d}"
        items_list = [{"id": it.id, "name": it.name, "price": it.price, "quantity": it.quantity} for it in order.items]
        order_record = OrderModel(
            id=order_id,
            owner_user_id=user.id,
            user_email=user.email,
            patient_name=user.name,
            items_json=json.dumps(items_list),
            total_amount=order.totalAmount,
            delivery_address=order.address,
            payment_method=order.paymentMethod,
            status="Confirmed - Preparing for Delivery",
        )
        session.add(order_record)
        session.commit()

        return {
            "status": "success",
            "orderId": order_id,
            "message": f"Order #{order_id} placed and recorded in SQL database! Delivery scheduled within 20-30 mins.",
            "summary": {
                "orderId": order_id,
                "totalAmount": order.totalAmount,
                "itemCount": len(order.items),
                "deliveryAddress": order.address,
                "paymentMethod": order.paymentMethod,
                "status": "Confirmed",
            },
        }
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

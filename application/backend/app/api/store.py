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
def get_medicines(category: Optional[str] = "all", search: Optional[str] = ""):
    medicines = [
        {
            "id": "m1",
            "name": "Paracetamol 650mg",
            "category": "Pain Relief",
            "price": 32.50,
            "originalPrice": 45.00,
            "discount": "28% OFF",
            "rating": 4.8,
            "reviews": 342,
            "dosage": "1 tablet every 6 hours post meals",
            "image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=300",
            "genericAlt": "Acetaminophen 650mg (₹18.00)",
            "requiresRx": False
        },
        {
            "id": "m2",
            "name": "Vitamin C 500mg (Zinc + D3)",
            "category": "Supplements",
            "price": 140.00,
            "originalPrice": 175.00,
            "discount": "20% OFF",
            "rating": 4.9,
            "reviews": 512,
            "dosage": "1 chewable tablet daily",
            "image": "https://images.unsplash.com/photo-1577401239170-897942555fb3?auto=format&fit=crop&q=80&w=300",
            "genericAlt": "Ascorbic Acid 500mg (₹75.00)",
            "requiresRx": False
        },
        {
            "id": "m3",
            "name": "Dolo 650mg Tablet",
            "category": "Pain Relief",
            "price": 30.00,
            "originalPrice": 38.00,
            "discount": "21% OFF",
            "rating": 4.7,
            "reviews": 890,
            "dosage": "1 tablet as prescribed by physician",
            "image": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=300",
            "genericAlt": "Paracetamol 650mg Generic (₹15.00)",
            "requiresRx": False
        },
        {
            "id": "m4",
            "name": "Amoxicillin 500mg Capsule",
            "category": "Antibiotics",
            "price": 88.00,
            "originalPrice": 110.00,
            "discount": "20% OFF",
            "rating": 4.6,
            "reviews": 128,
            "dosage": "1 capsule twice daily for 5 days",
            "image": "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?auto=format&fit=crop&q=80&w=300",
            "genericAlt": "Amox 500 Generic (₹42.00)",
            "requiresRx": True
        }
    ]

    if category and category != "all":
        medicines = [m for m in medicines if m["category"].lower() == category.lower()]

    if search:
        s = search.lower()
        medicines = [m for m in medicines if s in m["name"].lower() or s in m["category"].lower()]

    return {"status": "success", "count": len(medicines), "medicines": medicines}


@router.post("/orders")
def place_order(order: OrderRequest):
    if not order.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    return {
        "status": "success",
        "orderId": "ORD-982415",
        "message": "Order placed successfully! Delivery scheduled within 45 mins.",
        "summary": {
            "totalAmount": order.totalAmount,
            "itemCount": len(order.items),
            "deliveryAddress": order.address,
            "paymentMethod": order.paymentMethod
        }
    }

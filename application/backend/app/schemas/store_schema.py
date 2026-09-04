from typing import List, Optional
from pydantic import BaseModel, Field

class OrderItemSchema(BaseModel):
    id: Optional[str] = None
    name: str
    price: float
    quantity: int = 1
    image: Optional[str] = None

class OrderCreateRequest(BaseModel):
    userId: Optional[str] = None
    items: List[OrderItemSchema]
    totalAmount: float
    address: Optional[str] = "Plot 42, Jubilee Hills, Hyderabad, Telangana"
    paymentMethod: Optional[str] = "Cash on Delivery / UPI"

from pydantic import BaseModel
from typing import Optional

class OrderCreate(BaseModel):
    user_id: int
    total_amount: float
    currency: str
    payment_method: Optional[str]

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    currency: str
    status: str
    active: bool
    class Config:
        from_attributes = True

class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True
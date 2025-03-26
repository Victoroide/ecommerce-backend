from pydantic import BaseModel
from typing import Optional, List

# Shopping Cart schemas
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int

class ShoppingCartResponse(BaseModel):
    id: int
    user_id: int
    active: bool
    class Config:
        orm_mode = True

# Order schemas
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
        orm_mode = True

# Payment schemas
class PaymentCreate(BaseModel):
    order_id: int
    amount: float
    method: str

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    method: str
    status: str
    class Config:
        orm_mode = True

# Delivery schemas
class DeliveryCreate(BaseModel):
    order_id: int
    delivery_address: str

class DeliveryResponse(BaseModel):
    id: int
    order_id: int
    delivery_address: str
    delivery_status: str
    class Config:
        orm_mode = True

# Feedback schemas
class FeedbackCreate(BaseModel):
    order_id: int
    user_id: int
    rating: int
    comment: Optional[str]

class FeedbackResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    rating: int
    comment: Optional[str]
    class Config:
        orm_mode = True

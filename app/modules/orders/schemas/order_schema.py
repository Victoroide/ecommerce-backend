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
        orm_mode = True
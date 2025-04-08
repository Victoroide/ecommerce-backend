from pydantic import BaseModel
from typing import Optional

class PromotionCreate(BaseModel):
    title: str
    description: Optional[str]
    discount_percentage: float
    start_date: str  # ISO date
    end_date: str

class PromotionResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    discount_percentage: float
    start_date: str
    end_date: str
    active: bool

    class Config:
        from_attributes = True

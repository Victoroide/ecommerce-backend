from pydantic import BaseModel
from typing import Optional
from datetime import timedelta

class WarrantyCreate(BaseModel):
    product_id: int
    brand_id: int
    warranty_type: str
    details: Optional[str] = None
    duration: Optional[timedelta] = None

class WarrantyResponse(BaseModel):
    id: int
    product_id: int
    brand_id: int
    warranty_type: str
    details: Optional[str] = None
    duration: Optional[timedelta] = None

    class Config:
        orm_mode = True

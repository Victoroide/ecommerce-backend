from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .brand_schema import BrandResponse

class WarrantyBase(BaseModel):
    name: str
    description: Optional[str] = None
    duration_months: int

class WarrantyCreate(WarrantyBase):
    pass

class WarrantyResponse(WarrantyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    brand: Optional[BrandResponse] = None

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    brand_id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    model_3d_url: Optional[str] = None
    ar_url: Optional[str] = None
    technical_specifications: Optional[str] = None

class ProductUpdate(BaseModel):
    brand_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    technical_specifications: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    brand_id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    active: bool
    image_url: Optional[str] = None
    model_3d_url: Optional[str] = None
    ar_url: Optional[str] = None
    technical_specifications: Optional[str] = None

    class Config:
        from_attributes = True
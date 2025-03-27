from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    brand_id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    image_url: Optional[str]
    model_3d_url: Optional[str]
    ar_url: Optional[str]
    technical_specifications: Optional[str]
    warranty_info: Optional[str]

class ProductResponse(BaseModel):
    id: int
    brand_id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    active: bool
    image_url: Optional[str]
    model_3d_url: Optional[str]
    ar_url: Optional[str]
    technical_specifications: Optional[str]
    warranty_info: Optional[str]

    class Config:
        orm_mode = True
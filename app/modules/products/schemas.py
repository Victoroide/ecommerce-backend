from pydantic import BaseModel
from typing import Optional

class BrandCreate(BaseModel):
    name: str
    warranty_policy: Optional[str]

class BrandResponse(BaseModel):
    id: int
    name: str
    warranty_policy: Optional[str]
    active: bool

    class Config:
        orm_mode = True

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

class ProductCategoryResponse(BaseModel):
    id: int
    name: str
    active: bool

    class Config:
        orm_mode = True
class InventoryCreate(BaseModel):
    product_id: int
    stock: int
    price_usd: float

class InventoryResponse(BaseModel):
    id: int
    product_id: int
    stock: int
    price_usd: float
    price_bs: float

    class Config:
        orm_mode = True

class WarrantyCreate(BaseModel):
    product_id: int
    brand_id: int
    warranty_type: str
    details: Optional[str]
    duration: Optional[str]  # e.g., "12 months"

class WarrantyResponse(BaseModel):
    id: int
    product_id: int
    brand_id: int
    warranty_type: str
    details: Optional[str]
    duration: Optional[str]

    class Config:
        orm_mode = True

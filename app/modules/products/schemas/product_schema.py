from pydantic import BaseModel
from typing import Optional, List
from .brand_schema import BrandResponse
from .product_category_schema import ProductCategoryResponse
from .warranty_schema import WarrantyResponse

class ProductCreate(BaseModel):
    brand_id: int
    category_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    model_3d_url: Optional[str] = None
    ar_url: Optional[str] = None
    technical_specifications: Optional[str] = None

class ProductUpdate(BaseModel):
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    technical_specifications: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    brand_id: int
    brand: Optional[BrandResponse] = None
    category_id: Optional[int] = None
    category: Optional[ProductCategoryResponse] = None
    name: str
    description: Optional[str] = None
    active: bool
    image_url: Optional[str] = None
    model_3d_url: Optional[str] = None
    ar_url: Optional[str] = None
    technical_specifications: Optional[str] = None
    warranty: Optional[WarrantyResponse] = None

    class Config:
        orm_mode = True

class BulkProductCreate(BaseModel):
    products: List[ProductCreate]

class BulkProductResponse(BaseModel):
    message: str
    products: List[ProductResponse]
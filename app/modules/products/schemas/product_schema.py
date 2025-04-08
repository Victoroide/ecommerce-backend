from pydantic import BaseModel
from typing import Optional, List
from fastapi import Form
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

class ProductFormSchema(BaseModel):
    brand_id: int
    category_id: Optional[int] = None
    warranty_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    technical_specifications: Optional[str] = None

    @classmethod
    def as_form(cls,
        brand_id: int = Form(...),
        category_id: Optional[int] = Form(None),
        warranty_id: Optional[int] = Form(None),
        name: str = Form(...),
        description: Optional[str] = Form(None),
        technical_specifications: Optional[str] = Form(None)
    ):
        return cls(
            brand_id=brand_id,
            category_id=category_id,
            warranty_id=warranty_id,
            name=name,
            description=description,
            technical_specifications=technical_specifications
        )

class ProductUpdate(BaseModel):
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    technical_specifications: Optional[str] = None

class ProductFormPatchSchema(BaseModel):
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    technical_specifications: Optional[str] = None
    warranty_id: Optional[int] = None

    @classmethod
    def as_form(
        cls,
        brand_id: Optional[str] = Form(None),
        category_id: Optional[str] = Form(None),
        name: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        technical_specifications: Optional[str] = Form(None),
        warranty_id: Optional[str] = Form(None)
    ):
        def parse_int(value):
            return int(value) if value not in [None, ""] else None

        return cls(
            brand_id=parse_int(brand_id),
            category_id=parse_int(category_id),
            name=name or None,
            description=description or None,
            technical_specifications=technical_specifications or None,
            warranty_id=parse_int(warranty_id)
        )
    
class ProductResponse(BaseModel):
    id: int
    uuid: Optional[str]
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
        from_attributes = True

class BulkProductCreate(BaseModel):
    products: List[ProductCreate]

class BulkProductResponse(BaseModel):
    message: str
    products: List[ProductResponse]

class ProductMultipartCreate(BaseModel):
    index: int
    brand_id: int
    category_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    technical_specifications: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        index: int = Form(...),
        brand_id: int = Form(...),
        category_id: Optional[int] = Form(None),
        name: str = Form(...),
        description: Optional[str] = Form(None),
        technical_specifications: Optional[str] = Form(None),
    ):
        return cls(
            index=index,
            brand_id=brand_id,
            category_id=category_id,
            name=name,
            description=description,
            technical_specifications=technical_specifications,
        )
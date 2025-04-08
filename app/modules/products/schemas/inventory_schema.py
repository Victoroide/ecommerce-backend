from pydantic import BaseModel
from app.modules.products.schemas.product_schema import ProductResponse

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
    product: ProductResponse

    class Config:
        from_attributes = True
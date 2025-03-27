from pydantic import BaseModel

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
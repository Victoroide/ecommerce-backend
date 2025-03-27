from pydantic import BaseModel

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int

class ShoppingCartResponse(BaseModel):
    id: int
    user_id: int
    active: bool
    class Config:
        orm_mode = True
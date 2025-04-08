from pydantic import BaseModel

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int

class ShoppingCartResponse(BaseModel):
    id: int
    user_id: int
    active: bool
    class Config:
        from_attributes = True

class CartItemResponse(BaseModel):
    id: int
    cart_id: int
    product_id: int
    quantity: int
    class Config:
        from_attributes = True
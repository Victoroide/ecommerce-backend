from pydantic import BaseModel

class DeliveryCreate(BaseModel):
    order_id: int
    delivery_address: str

class DeliveryResponse(BaseModel):
    id: int
    order_id: int
    delivery_address: str
    delivery_status: str
    class Config:
        from_attributes = True
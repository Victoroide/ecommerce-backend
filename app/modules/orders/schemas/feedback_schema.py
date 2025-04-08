from pydantic import BaseModel
from typing import Optional

class FeedbackCreate(BaseModel):
    order_id: int
    user_id: int
    rating: int
    comment: Optional[str]

class FeedbackResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    rating: int
    comment: Optional[str]
    class Config:
        from_attributes = True

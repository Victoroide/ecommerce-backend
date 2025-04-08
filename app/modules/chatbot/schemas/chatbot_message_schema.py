from pydantic import BaseModel
from typing import Optional

class ChatbotMessageCreate(BaseModel):
    session_id: int
    sender: str
    message: str

class ChatbotMessageResponse(BaseModel):
    id: int
    session_id: int
    sender: str
    message: str

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import Optional

class ChatbotSessionCreate(BaseModel):
    user_id: Optional[int] = None
    session_token: str
    status: str

class ChatbotSessionResponse(BaseModel):
    id: int
    user_id: Optional[int]
    session_token: str
    status: str

    class Config:
        from_attributes = True
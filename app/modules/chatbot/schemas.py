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
        orm_mode = True

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
        orm_mode = True

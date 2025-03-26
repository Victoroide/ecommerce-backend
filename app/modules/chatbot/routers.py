from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.modules.chatbot.models import ChatbotSession, ChatbotMessage
from app.modules.chatbot.schemas import ChatbotSessionCreate, ChatbotSessionResponse, ChatbotMessageCreate, ChatbotMessageResponse

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/session", response_model=ChatbotSessionResponse)
def create_session(session_data: ChatbotSessionCreate, db: Session = Depends(get_db)):
    session = ChatbotSession(**session_data.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.post("/message", response_model=ChatbotMessageResponse)
def send_message(message_data: ChatbotMessageCreate, db: Session = Depends(get_db)):
    message = ChatbotMessage(**message_data.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

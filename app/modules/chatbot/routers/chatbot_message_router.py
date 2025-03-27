from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import SessionLocal
from app.modules.chatbot.models import ChatbotMessage, ChatbotSession
from app.modules.chatbot.schemas import ChatbotMessageCreate, ChatbotMessageResponse

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/messages", response_model=ChatbotMessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(message_data: ChatbotMessageCreate, db: Session = Depends(get_db)):
    session = db.query(ChatbotSession).filter(
        ChatbotSession.id == message_data.session_id, 
        ChatbotSession.active == True
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chatbot session not found or inactive.")
    
    if message_data.sender not in ["user", "bot"]:
        raise HTTPException(status_code=400, detail="Sender must be 'user' or 'bot'.")
    
    message = ChatbotMessage(
        session_id=message_data.session_id,
        sender=message_data.sender,
        message=message_data.message
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

@router.get("/sessions/{session_id}/messages", response_model=List[ChatbotMessageResponse])
def get_session_messages(session_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    session = db.query(ChatbotSession).filter(
        ChatbotSession.id == session_id, 
        ChatbotSession.active == True
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chatbot session not found or inactive.")
    
    messages = db.query(ChatbotMessage).filter(ChatbotMessage.session_id == session_id).offset(skip).limit(limit).all()
    return messages

@router.get("/messages/{message_id}", response_model=ChatbotMessageResponse)
def get_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(ChatbotMessage).filter(ChatbotMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found.")
    
    session = db.query(ChatbotSession).filter(
        ChatbotSession.id == message.session_id, 
        ChatbotSession.active == True
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Associated chatbot session not found or inactive.")
    
    return message

@router.patch("/messages/{message_id}", response_model=ChatbotMessageResponse)
def update_message(message_id: int, message_data: ChatbotMessageCreate, db: Session = Depends(get_db)):
    message = db.query(ChatbotMessage).filter(ChatbotMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found.")
    
    session = db.query(ChatbotSession).filter(
        ChatbotSession.id == message_data.session_id, 
        ChatbotSession.active == True
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chatbot session not found or inactive.")
    
    if message_data.sender not in ["user", "bot"]:
        raise HTTPException(status_code=400, detail="Sender must be 'user' or 'bot'.")
    
    for key, value in message_data:
        setattr(message, key, value)
    
    db.commit()
    db.refresh(message)
    return message

@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(ChatbotMessage).filter(ChatbotMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found.")
    
    db.delete(message)
    db.commit()
    return None
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import SessionLocal
from app.modules.chatbot.models import ChatbotSession, ChatbotMessage
from app.modules.chatbot.schemas import *

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ChatBotSession CRUD ---

@router.post("/sessions", response_model=ChatbotSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session_data: ChatbotSessionCreate, db: Session = Depends(get_db)):
    existing = db.query(ChatbotSession).filter(ChatbotSession.session_token == session_data.session_token).first()
    if existing:
        raise HTTPException(status_code=400, detail="Session token already exists.")
    
    session = ChatbotSession(
        user_id=session_data.user_id,
        session_token=session_data.session_token,
        active=True
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatbotSessionResponse])
def get_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sessions = db.query(ChatbotSession).filter(ChatbotSession.active == True).offset(skip).limit(limit).all()
    return sessions

@router.get("/sessions/{session_id}", response_model=ChatbotSessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatbotSession).filter(ChatbotSession.id == session_id, ChatbotSession.active == True).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chatbot session not found.")
    return session

@router.patch("/sessions/{session_id}", response_model=ChatbotSessionResponse)
def update_session(session_id: int, session_data: ChatbotSessionCreate, db: Session = Depends(get_db)):
    session = db.query(ChatbotSession).filter(ChatbotSession.id == session_id, ChatbotSession.active == True).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chatbot session not found.")
    
    if session_data.session_token != session.session_token:
        existing = db.query(ChatbotSession).filter(
            ChatbotSession.session_token == session_data.session_token, 
            ChatbotSession.id != session_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Session token already exists.")
    
    session.session_token = session_data.session_token
    if session_data.user_id is not None:
        session.user_id = session_data.user_id
    
    db.commit()
    db.refresh(session)
    return session

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatbotSession).filter(ChatbotSession.id == session_id, ChatbotSession.active == True).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chatbot session not found.")
    
    session.active = False
    db.commit()
    return None

# --- ChatBotMessage CRUD ---

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
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import SessionLocal
from app.modules.chatbot.models import ChatbotSession
from app.modules.chatbot.schemas import ChatbotSessionCreate, ChatbotSessionResponse

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
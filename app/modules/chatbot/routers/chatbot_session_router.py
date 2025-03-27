from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.chatbot.models import ChatbotSession
from app.modules.chatbot.schemas import ChatbotSessionCreate, ChatbotSessionResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/sessions", response_model=ChatbotSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(session_data: ChatbotSessionCreate, db: Session = Depends(get_db)):
    existing = db.query(ChatbotSession).filter(ChatbotSession.session_token == session_data.session_token).first()
    if existing:
        raise HTTPException(status_code=400, detail="Session token already exists.")
    
    try:
        with db.begin_nested():
            session = ChatbotSession(
                user_id=session_data.user_id,
                session_token=session_data.session_token,
                active=True
            )
            db.add(session)
            db.flush()
        db.commit()
        return session
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/sessions", response_model=PagedResponse[ChatbotSessionResponse])
def get_sessions(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc"),
    user_id: Optional[int] = Query(None)
):
    query = db.query(ChatbotSession).filter(ChatbotSession.active == True)
    
    if user_id:
        query = query.filter(ChatbotSession.user_id == user_id)
    
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination)

@router.get("/sessions/{session_id}", response_model=ChatbotSessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatbotSession).filter(
        and_(ChatbotSession.id == session_id, ChatbotSession.active == True)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chatbot session not found.")
    
    return session

@router.patch("/sessions/{session_id}", response_model=ChatbotSessionResponse)
def update_session(session_id: int, session_data: ChatbotSessionCreate, db: Session = Depends(get_db)):
    session = db.query(ChatbotSession).filter(
        and_(ChatbotSession.id == session_id, ChatbotSession.active == True)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chatbot session not found.")
    
    if session_data.session_token != session.session_token:
        existing = db.query(ChatbotSession).filter(
            ChatbotSession.session_token == session_data.session_token, 
            ChatbotSession.id != session_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Session token already exists.")
    
    try:
        with db.begin_nested():
            session.session_token = session_data.session_token
            if session_data.user_id is not None:
                session.user_id = session_data.user_id
            db.flush()
        db.commit()
        return session
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatbotSession).filter(
        and_(ChatbotSession.id == session_id, ChatbotSession.active == True)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chatbot session not found.")
    
    try:
        with db.begin_nested():
            session.active = False
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
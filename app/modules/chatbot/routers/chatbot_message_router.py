from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.chatbot.models import ChatbotMessage, ChatbotSession
from app.modules.chatbot.schemas import ChatbotMessageCreate, ChatbotMessageResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate

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
        and_(ChatbotSession.id == message_data.session_id, ChatbotSession.active == True)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chatbot session not found or inactive.")
    
    if message_data.sender not in ["user", "bot"]:
        raise HTTPException(status_code=400, detail="Sender must be 'user' or 'bot'.")
    
    try:
        with db.begin_nested():
            message = ChatbotMessage(
                session_id=message_data.session_id,
                sender=message_data.sender,
                message=message_data.message
            )
            db.add(message)
            db.flush()
        db.commit()
        return message
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/sessions/{session_id}/messages", response_model=PagedResponse[ChatbotMessageResponse])
def get_session_messages(
    session_id: int, 
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("id"),
    sort_order: str = Query("asc")
):
    session = db.query(ChatbotSession).filter(
        and_(ChatbotSession.id == session_id, ChatbotSession.active == True)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chatbot session not found or inactive.")
    
    query = db.query(ChatbotMessage).filter(ChatbotMessage.session_id == session_id)
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    
    return paginate(query, pagination, ChatbotMessageResponse)

@router.get("/messages/{message_id}", response_model=ChatbotMessageResponse)
def get_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(ChatbotMessage).filter(ChatbotMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found.")
    
    session = db.query(ChatbotSession).filter(
        and_(ChatbotSession.id == message.session_id, ChatbotSession.active == True)
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
        and_(ChatbotSession.id == message_data.session_id, ChatbotSession.active == True)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chatbot session not found or inactive.")
    
    if message_data.sender not in ["user", "bot"]:
        raise HTTPException(status_code=400, detail="Sender must be 'user' or 'bot'.")
    
    try:
        with db.begin_nested():
            message.session_id = message_data.session_id
            message.sender = message_data.sender
            message.message = message_data.message
            db.flush()
        db.commit()
        return message
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: int, db: Session = Depends(get_db)):
    message = db.query(ChatbotMessage).filter(ChatbotMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found.")
    
    try:
        with db.begin_nested():
            db.delete(message)
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
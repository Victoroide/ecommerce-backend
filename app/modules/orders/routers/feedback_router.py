from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.orders.models import Feedback, Order
from app.modules.orders.schemas.feedback_schema import FeedbackCreate, FeedbackResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate

router = APIRouter(prefix="/orders", tags=["orders"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(feedback_data: FeedbackCreate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        and_(Order.id == feedback_data.order_id, Order.active == True)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    if order.status != "delivered":
        raise HTTPException(status_code=400, detail="Feedback can only be left for delivered orders.")
    
    existing_feedback = db.query(Feedback).filter(
        and_(Feedback.order_id == feedback_data.order_id, Feedback.user_id == feedback_data.user_id)
    ).first()
    
    if existing_feedback:
        raise HTTPException(status_code=400, detail="Feedback already exists for this order from this user.")
    
    if feedback_data.rating < 1 or feedback_data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
    
    try:
        with db.begin_nested():
            feedback = Feedback(
                order_id=feedback_data.order_id,
                user_id=feedback_data.user_id,
                rating=feedback_data.rating,
                comment=feedback_data.comment
            )
            db.add(feedback)
            db.flush()
        db.commit()
        return feedback
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/feedback", response_model=PagedResponse[FeedbackResponse])
def get_feedback(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("id"),
    sort_order: str = Query("desc"),
    rating: Optional[int] = Query(None)
):
    query = db.query(Feedback)
    
    if rating:
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=400, detail="Rating filter must be between 1 and 5.")
        query = query.filter(Feedback.rating == rating)
    
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination)

@router.get("/feedback/order/{order_id}", response_model=List[FeedbackResponse])
def get_order_feedback(order_id: int, db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.order_id == order_id).all()
    return feedback

@router.get("/feedback/user/{user_id}", response_model=PagedResponse[FeedbackResponse])
def get_user_feedback(
    user_id: int, 
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("id"),
    sort_order: str = Query("desc")
):
    query = db.query(Feedback).filter(Feedback.user_id == user_id)
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination)

@router.patch("/feedback/{feedback_id}", response_model=FeedbackResponse)
def update_feedback(
    feedback_id: int, 
    rating: Optional[int] = None, 
    comment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found.")
    
    try:
        with db.begin_nested():
            if rating is not None:
                if rating < 1 or rating > 5:
                    raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
                feedback.rating = rating
            
            if comment is not None:
                feedback.comment = comment
            
            db.flush()
        db.commit()
        return feedback
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(feedback_id: int, db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found.")
    
    try:
        with db.begin_nested():
            db.delete(feedback)
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
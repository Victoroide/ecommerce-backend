from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.orders.models import Order, Payment
from app.modules.orders.schemas.payment_schema import PaymentCreate, PaymentResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate

router = APIRouter(prefix="/orders", tags=["orders"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payment_data: PaymentCreate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        and_(Order.id == payment_data.order_id, Order.active == True)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    existing_payment = db.query(Payment).filter(Payment.order_id == payment_data.order_id).first()
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment already exists for this order.")
    
    try:
        with db.begin_nested():
            payment = Payment(
                order_id=payment_data.order_id,
                amount=payment_data.amount,
                method=payment_data.method,
                status="initiated"
            )
            db.add(payment)
            
            # Update order status to paid
            order.status = "paid"
            db.flush()
        db.commit()
        return payment
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/payments", response_model=PagedResponse[PaymentResponse])
def get_payments(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc"),
    status: Optional[str] = Query(None)
):
    query = db.query(Payment)
    
    if status:
        query = query.filter(Payment.status == status)
    
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination)

@router.get("/payments/order/{order_id}", response_model=PaymentResponse)
def get_order_payment(order_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found for this order.")
    return payment

@router.patch("/payments/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: int, 
    status: str, 
    transaction_id: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")
    
    valid_statuses = ["initiated", "completed", "failed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    try:
        with db.begin_nested():
            payment.status = status
            
            if transaction_id:
                payment.transaction_id = transaction_id
            
            # If payment failed, update order status
            if status == "failed":
                order = db.query(Order).filter(Order.id == payment.order_id).first()
                if order:
                    order.status = "pending"
            
            db.flush()
        db.commit()
        return payment
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
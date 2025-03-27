from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import SessionLocal
from app.modules.orders.models import Order, Payment
from app.modules.orders.schemas.payment_schema import *

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
        Order.id == payment_data.order_id, 
        Order.active == True
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    existing_payment = db.query(Payment).filter(Payment.order_id == payment_data.order_id).first()
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment already exists for this order.")
    
    payment = Payment(
        order_id=payment_data.order_id,
        amount=payment_data.amount,
        method=payment_data.method,
        status="initiated"
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    order.status = "paid"
    db.commit()
    
    return payment

@router.get("/payments/order/{order_id}", response_model=PaymentResponse)
def get_order_payment(order_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found for this order.")
    return payment

@router.patch("/payments/{payment_id}", response_model=PaymentResponse)
def update_payment(payment_id: int, status: str, transaction_id: str = None, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")
    
    valid_statuses = ["initiated", "completed", "failed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    payment.status = status
    if transaction_id:
        payment.transaction_id = transaction_id
    
    db.commit()
    db.refresh(payment)
    return payment
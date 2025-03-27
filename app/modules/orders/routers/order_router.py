from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import SessionLocal
from app.modules.orders.models import Order, OrderItem
from app.modules.orders.schemas.order_schema import *

router = APIRouter(prefix="/orders", tags=["orders"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    order = Order(
        user_id=order_data.user_id,
        total_amount=order_data.total_amount,
        currency=order_data.currency,
        payment_method=order_data.payment_method,
        status="pending",
        active=True
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.get("/", response_model=List[OrderResponse])
def get_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.active == True).offset(skip).limit(limit).all()
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order

@router.get("/user/{user_id}", response_model=List[OrderResponse])
def get_user_orders(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(
        Order.user_id == user_id,
        Order.active == True
    ).all()
    return orders

@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int, 
    status: str = None, 
    payment_method: str = None,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id, Order.active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    if status is not None:
        valid_statuses = ["pending", "paid", "shipped", "delivered", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        order.status = status
    
    if payment_method is not None:
        valid_methods = ["qr", "paypal", "stripe"]
        if payment_method not in valid_methods:
            raise HTTPException(status_code=400, detail=f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")
        order.payment_method = payment_method
    
    db.commit()
    db.refresh(order)
    return order

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    order.active = False
    db.commit()
    return None

# --- Order Item ---

@router.post("/{order_id}/items", status_code=status.HTTP_201_CREATED)
def add_order_item(order_id: int, product_id: int, quantity: int, unit_price: float, db: Session = Depends(get_db)):
    # Verify order exists and is active
    order = db.query(Order).filter(Order.id == order_id, Order.active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    order_item = OrderItem(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price
    )
    
    db.add(order_item)
    db.commit()
    db.refresh(order_item)
    return order_item

@router.get("/{order_id}/items")
def get_order_items(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return items
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.orders.models import Order, OrderItem
from app.modules.orders.schemas.order_schema import OrderCreate, OrderResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate

router = APIRouter(prefix="/orders", tags=["orders"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    try:
        with db.begin_nested():
            order = Order(
                user_id=order_data.user_id,
                total_amount=order_data.total_amount,
                currency=order_data.currency,
                payment_method=order_data.payment_method,
                status="pending",
                active=True
            )
            db.add(order)
            db.flush()
        db.commit()
        return order
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/", response_model=PagedResponse[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc"),
    status: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None)
):
    query = db.query(Order).filter(Order.active == True)
    
    if status:
        query = query.filter(Order.status == status)
    
    if user_id:
        query = query.filter(Order.user_id == user_id)
    
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination)

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.active == True)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order

@router.get("/user/{user_id}", response_model=PagedResponse[OrderResponse])
def get_user_orders(
    user_id: int, 
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("id"),
    sort_order: str = Query("desc"),
    status: Optional[str] = Query(None)
):
    query = db.query(Order).filter(
        and_(Order.user_id == user_id, Order.active == True)
    )
    
    if status:
        query = query.filter(Order.status == status)
    
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination)

@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int, 
    status: Optional[str] = None, 
    payment_method: Optional[str] = None,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.active == True)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    try:
        with db.begin_nested():
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
            
            db.flush()
        db.commit()
        return order
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.active == True)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    try:
        with db.begin_nested():
            order.active = False
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# --- Order Item ---
@router.post("/{order_id}/items", status_code=status.HTTP_201_CREATED)
def add_order_item(order_id: int, product_id: int, quantity: int, unit_price: float, db: Session = Depends(get_db)):
    # Verify order exists and is active
    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.active == True)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    try:
        with db.begin_nested():
            order_item = OrderItem(
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price
            )
            db.add(order_item)
            db.flush()
        db.commit()
        return order_item
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{order_id}/items")
def get_order_items(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.active == True)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return items
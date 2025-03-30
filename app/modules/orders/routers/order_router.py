from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.authentication.models.user import User
from app.modules.orders.models import Order, OrderItem
from app.modules.orders.schemas.order_schema import OrderCreate, OrderResponse, OrderItemResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate
from app.modules.authentication.dependencies import get_current_user, get_admin_user, verify_user_access, verify_order_access

router = APIRouter(prefix="/orders", tags=["orders"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if order_data.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create orders for other users"
        )
        
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
    current_user: User = Depends(get_admin_user),
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
    return paginate(query, pagination, OrderResponse)

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order: Order = Depends(verify_order_access()),
    db: Session = Depends(get_db)
):
    return order

@router.get("/user/{user_id}", response_model=PagedResponse[OrderResponse])
def get_user_orders(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_user_access()),
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
    return paginate(query, pagination, OrderResponse)

@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order: Order = Depends(verify_order_access()),
    status: Optional[str] = None, 
    payment_method: Optional[str] = None,
    db: Session = Depends(get_db)
):
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
def delete_order(
    order: Order = Depends(verify_order_access()),
    db: Session = Depends(get_db)
):
    try:
        with db.begin_nested():
            order.active = False
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/{order_id}/items", response_model=OrderItemResponse, status_code=status.HTTP_201_CREATED)
def add_order_item(
    order: Order = Depends(verify_order_access()),
    product_id: int = None, 
    quantity: int = None, 
    unit_price: float = None, 
    db: Session = Depends(get_db)
):
    try:
        with db.begin_nested():
            order_item = OrderItem(
                order_id=order.id,
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

@router.get("/{order_id}/items", response_model=PagedResponse[OrderItemResponse])
def get_order_items(
    order: Order = Depends(verify_order_access()),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc")
):
    query = db.query(OrderItem).filter(OrderItem.order_id == order.id)
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination, OrderItemResponse)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.orders.models import Delivery, Order
from app.modules.orders.schemas.delivery_schema import DeliveryCreate, DeliveryResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate

router = APIRouter(prefix="/orders", tags=["orders"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/deliveries", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
def create_delivery(delivery_data: DeliveryCreate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        and_(Order.id == delivery_data.order_id, Order.active == True)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    if order.status not in ["paid", "shipped"]:
        raise HTTPException(status_code=400, detail="Order must be paid before creating delivery.")
    
    existing_delivery = db.query(Delivery).filter(Delivery.order_id == delivery_data.order_id).first()
    if existing_delivery:
        raise HTTPException(status_code=400, detail="Delivery already exists for this order.")
    
    try:
        with db.begin_nested():
            delivery = Delivery(
                order_id=delivery_data.order_id,
                delivery_address=delivery_data.delivery_address,
                delivery_status="pending",
                tracking_info=None,
                estimated_arrival=None
            )
            db.add(delivery)
            
            # Update order status to shipped if it was only paid
            if order.status == "paid":
                order.status = "shipped"
            
            db.flush()
        db.commit()
        return delivery
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/deliveries", response_model=PagedResponse[DeliveryResponse])
def get_deliveries(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc"),
    status: Optional[str] = Query(None)
):
    query = db.query(Delivery)
    
    if status:
        query = query.filter(Delivery.delivery_status == status)
    
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination, DeliveryResponse)

@router.get("/deliveries/order/{order_id}", response_model=DeliveryResponse)
def get_order_delivery(order_id: int, db: Session = Depends(get_db)):
    delivery = db.query(Delivery).filter(Delivery.order_id == order_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found for this order.")
    return delivery

@router.patch("/deliveries/{delivery_id}", response_model=DeliveryResponse)
def update_delivery(
    delivery_id: int, 
    status: Optional[str] = None, 
    tracking_info: Optional[str] = None, 
    estimated_arrival: Optional[str] = None,
    db: Session = Depends(get_db)
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found.")
    
    try:
        with db.begin_nested():
            if status is not None:
                valid_statuses = ["pending", "in_transit", "delivered", "cancelled"]
                if status not in valid_statuses:
                    raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
                
                delivery.delivery_status = status
                
                # Update order status if delivery is delivered or cancelled
                if status == "delivered":
                    order = db.query(Order).filter(Order.id == delivery.order_id).first()
                    if order:
                        order.status = "delivered"
                elif status == "cancelled":
                    order = db.query(Order).filter(Order.id == delivery.order_id).first()
                    if order and order.status != "delivered":
                        order.status = "cancelled"
            
            if tracking_info is not None:
                delivery.tracking_info = tracking_info
            
            if estimated_arrival is not None:
                delivery.estimated_arrival = estimated_arrival
            
            db.flush()
        db.commit()
        return delivery
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import SessionLocal
from app.modules.orders.models import Delivery, Order
from app.modules.orders.schemas.delivery_schema import *

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
        Order.id == delivery_data.order_id, 
        Order.active == True
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    if order.status not in ["paid", "shipped"]:
        raise HTTPException(status_code=400, detail="Order must be paid before creating delivery.")
    
    existing_delivery = db.query(Delivery).filter(Delivery.order_id == delivery_data.order_id).first()
    if existing_delivery:
        raise HTTPException(status_code=400, detail="Delivery already exists for this order.")
    
    delivery = Delivery(
        order_id=delivery_data.order_id,
        delivery_address=delivery_data.delivery_address,
        delivery_status="pending",
        tracking_info=None,
        estimated_arrival=None
    )
    
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    
    if order.status == "paid":
        order.status = "shipped"
        db.commit()
    
    return delivery

@router.get("/deliveries/order/{order_id}", response_model=DeliveryResponse)
def get_order_delivery(order_id: int, db: Session = Depends(get_db)):
    delivery = db.query(Delivery).filter(Delivery.order_id == order_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found for this order.")
    return delivery

@router.patch("/deliveries/{delivery_id}", response_model=DeliveryResponse)
def update_delivery(
    delivery_id: int, 
    status: str = None, 
    tracking_info: str = None, 
    estimated_arrival: str = None,
    db: Session = Depends(get_db)
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found.")
    
    if status is not None:
        valid_statuses = ["pending", "in_transit", "delivered", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        delivery.delivery_status = status
        
        if status == "delivered":
            order = db.query(Order).filter(Order.id == delivery.order_id).first()
            if order:
                order.status = "delivered"
                db.commit()
    
    if tracking_info is not None:
        delivery.tracking_info = tracking_info
    
    if estimated_arrival is not None:
        delivery.estimated_arrival = estimated_arrival
    
    db.commit()
    db.refresh(delivery)
    return delivery
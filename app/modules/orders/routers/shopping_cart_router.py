from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.orders.models import ShoppingCart
from app.modules.orders.schemas.shopping_cart_schema import ShoppingCartResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate

router = APIRouter(prefix="/orders", tags=["orders"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/carts", response_model=ShoppingCartResponse, status_code=status.HTTP_201_CREATED)
def create_cart(user_id: int, db: Session = Depends(get_db)):
    existing_cart = db.query(ShoppingCart).filter(
        and_(ShoppingCart.user_id == user_id, ShoppingCart.active == True)
    ).first()
    
    if existing_cart:
        return existing_cart
    
    try:
        with db.begin_nested():
            cart = ShoppingCart(user_id=user_id, active=True)
            db.add(cart)
            db.flush()
        db.commit()
        return cart
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/carts", response_model=PagedResponse[ShoppingCartResponse])
def get_carts(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("id"),
    sort_order: str = Query("asc"),
    active_only: bool = True
):
    query = db.query(ShoppingCart)
    
    if active_only:
        query = query.filter(ShoppingCart.active == True)
    
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination)

@router.get("/carts/user/{user_id}", response_model=ShoppingCartResponse)
def get_user_cart(user_id: int, db: Session = Depends(get_db)):
    cart = db.query(ShoppingCart).filter(
        and_(ShoppingCart.user_id == user_id, ShoppingCart.active == True)
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="No active shopping cart found for this user.")
    
    return cart

@router.get("/carts/{cart_id}", response_model=ShoppingCartResponse)
def get_cart(cart_id: int, db: Session = Depends(get_db)):
    cart = db.query(ShoppingCart).filter(ShoppingCart.id == cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found.")
    return cart

@router.delete("/carts/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart(cart_id: int, db: Session = Depends(get_db)):
    cart = db.query(ShoppingCart).filter(
        and_(ShoppingCart.id == cart_id, ShoppingCart.active == True)
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found or already inactive.")
    
    try:
        with db.begin_nested():
            cart.active = False
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
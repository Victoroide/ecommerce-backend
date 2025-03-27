from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.modules.orders.models import ShoppingCart 
from app.modules.orders.schemas.shopping_cart_schema import *

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
        ShoppingCart.user_id == user_id,
        ShoppingCart.active == True
    ).first()
    
    if existing_cart:
        return existing_cart
    
    cart = ShoppingCart(user_id=user_id, active=True)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart

@router.get("/carts/user/{user_id}", response_model=ShoppingCartResponse)
def get_user_cart(user_id: int, db: Session = Depends(get_db)):
    cart = db.query(ShoppingCart).filter(
        ShoppingCart.user_id == user_id,
        ShoppingCart.active == True
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
        ShoppingCart.id == cart_id,
        ShoppingCart.active == True
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found or already inactive.")
    
    cart.active = False
    db.commit()
    return None
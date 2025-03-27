from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.orders.models import CartItem, ShoppingCart
from app.modules.orders.schemas.shopping_cart_schema import CartItemCreate, ShoppingCartResponse

router = APIRouter(prefix="/orders", tags=["orders"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/carts/{cart_id}/items", status_code=status.HTTP_201_CREATED)
def add_cart_item(cart_id: int, item_data: CartItemCreate, db: Session = Depends(get_db)):
    cart = db.query(ShoppingCart).filter(
        and_(ShoppingCart.id == cart_id, ShoppingCart.active == True)
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found or inactive.")
    
    existing_item = db.query(CartItem).filter(
        and_(CartItem.cart_id == cart_id, CartItem.product_id == item_data.product_id)
    ).first()
    
    try:
        with db.begin_nested():
            if existing_item:
                existing_item.quantity += item_data.quantity
                cart_item = existing_item
            else:
                cart_item = CartItem(
                    cart_id=cart_id,
                    product_id=item_data.product_id,
                    quantity=item_data.quantity
                )
                db.add(cart_item)
            
            db.flush()
        db.commit()
        return cart_item
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/carts/{cart_id}/items")
def get_cart_items(cart_id: int, db: Session = Depends(get_db)):
    cart = db.query(ShoppingCart).filter(
        and_(ShoppingCart.id == cart_id, ShoppingCart.active == True)
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found or inactive.")
    
    items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    return items

@router.patch("/carts/items/{item_id}")
def update_cart_item(item_id: int, quantity: int, db: Session = Depends(get_db)):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")
    
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    
    cart = db.query(ShoppingCart).filter(
        and_(ShoppingCart.id == item.cart_id, ShoppingCart.active == True)
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Associated shopping cart is inactive.")
    
    try:
        with db.begin_nested():
            item.quantity = quantity
            db.flush()
        db.commit()
        return item
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/carts/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    
    try:
        with db.begin_nested():
            db.delete(item)
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
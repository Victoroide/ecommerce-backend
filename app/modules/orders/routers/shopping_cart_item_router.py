from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import SessionLocal
from app.modules.orders.models import CartItem, ShoppingCart
from app.modules.orders.schemas.shopping_cart_schema import *

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
        ShoppingCart.id == cart_id,
        ShoppingCart.active == True
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found or inactive.")
    
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart_id,
        CartItem.product_id == item_data.product_id
    ).first()
    
    if existing_item:
        existing_item.quantity += item_data.quantity
        db.commit()
        db.refresh(existing_item)
        return existing_item
    
    cart_item = CartItem(
        cart_id=cart_id,
        product_id=item_data.product_id,
        quantity=item_data.quantity
    )
    
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item

@router.get("/carts/{cart_id}/items")
def get_cart_items(cart_id: int, db: Session = Depends(get_db)):
    cart = db.query(ShoppingCart).filter(
        ShoppingCart.id == cart_id,
        ShoppingCart.active == True
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
        ShoppingCart.id == item.cart_id,
        ShoppingCart.active == True
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Associated shopping cart is inactive.")
    
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item

@router.delete("/carts/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    
    db.delete(item)
    db.commit()
    return None
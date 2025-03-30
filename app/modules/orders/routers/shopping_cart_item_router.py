from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.authentication.models.user import User
from app.modules.orders.models import CartItem, ShoppingCart
from app.modules.orders.schemas.shopping_cart_schema import CartItemCreate, CartItemResponse
from app.modules.authentication.dependencies import get_current_user, get_admin_user
from app.core.pagination import PaginationParams, PagedResponse, paginate

router = APIRouter(prefix="/orders", tags=["orders"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/carts/{cart_id}/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_cart_item(
    cart_id: int, 
    item_data: CartItemCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cart = db.query(ShoppingCart).filter(
        and_(ShoppingCart.id == cart_id, ShoppingCart.active == True)
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found or inactive.")
    
    if current_user.id != cart.user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this shopping cart"
        )
    
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

@router.get("/carts/{cart_id}/items", response_model=PagedResponse[CartItemResponse])
def get_cart_items(
    cart_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc")
):
    cart = db.query(ShoppingCart).filter(
        and_(ShoppingCart.id == cart_id, ShoppingCart.active == True)
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found or inactive.")
    
    if current_user.id != cart.user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this shopping cart"
        )
    
    query = db.query(CartItem).filter(CartItem.cart_id == cart_id)
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination, CartItemResponse)

@router.patch("/carts/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(
    item_id: int, 
    quantity: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    
    if current_user.id != cart.user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this cart item"
        )
    
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
def remove_cart_item(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    
    cart = db.query(ShoppingCart).filter(ShoppingCart.id == item.cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Associated shopping cart not found.")
    
    if current_user.id != cart.user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this cart item"
        )
    
    try:
        with db.begin_nested():
            db.delete(item)
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
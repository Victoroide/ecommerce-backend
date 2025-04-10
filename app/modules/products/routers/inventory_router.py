from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from app.core.db import SessionLocal
from app.modules.products.models import Inventory, Product
from app.modules.products.schemas.inventory_schema import InventoryCreate, InventoryResponse
from app.modules.authentication.dependencies import get_current_user, get_admin_user
from app.modules.authentication.models.user import User
from app.core.pagination import PaginationParams, PagedResponse, paginate

router = APIRouter(prefix="/products", tags=["products"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/inventory", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory(
    inv_data: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(and_(Product.id == inv_data.product_id, Product.active == True)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(Inventory).filter(Inventory.product_id == inv_data.product_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Inventory already exists for this product")

    try:
        with db.begin_nested():
            inventory = Inventory(
                product_id=inv_data.product_id,
                stock=inv_data.stock,
                price_usd=inv_data.price_usd,
                price_bs=inv_data.price_usd * 13
            )
            db.add(inventory)
            db.flush()
        db.commit()
        return inventory
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/inventory", response_model=PagedResponse[InventoryResponse])
def get_inventories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc")
):
    query = db.query(Inventory)
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination, InventoryResponse)

@router.get("/inventory/{product_id:int}", response_model=InventoryResponse)
def get_product_inventory(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found for this product")
    return inventory

@router.patch("/inventory/{inventory_id:int}", response_model=InventoryResponse)
def update_inventory(
    inventory_id: int,
    stock: Optional[int] = None,
    price_usd: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")

    try:
        with db.begin_nested():
            if stock is not None:
                if stock < 0:
                    raise HTTPException(status_code=400, detail="Stock cannot be negative")
                inventory.stock = stock

            if price_usd is not None:
                if price_usd <= 0:
                    raise HTTPException(status_code=400, detail="Price must be greater than zero")
                inventory.price_usd = price_usd
                inventory.price_bs = price_usd * 13

            db.flush()
        db.commit()
        return inventory
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/inventory/{inventory_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")

    try:
        with db.begin_nested():
            db.delete(inventory)
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
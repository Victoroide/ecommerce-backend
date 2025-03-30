from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.products.models import Warranty, Product, Brand
from app.modules.products.schemas.warranty_schema import WarrantyCreate, WarrantyResponse
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

@router.post("/warranties", response_model=WarrantyResponse, status_code=status.HTTP_201_CREATED)
def create_warranty(
    warranty_data: WarrantyCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(
        and_(Product.id == warranty_data.product_id, Product.active == True)
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    brand = db.query(Brand).filter(
        and_(Brand.id == warranty_data.brand_id, Brand.active == True)
    ).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    existing = db.query(Warranty).filter(
        Warranty.product_id == warranty_data.product_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Warranty already exists for this product")
    
    try:
        with db.begin_nested():
            warranty = Warranty(**warranty_data.model_dump())
            db.add(warranty)
            db.flush()
        db.commit()
        return warranty
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/warranties", response_model=PagedResponse[WarrantyResponse])
def get_warranties(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc")
):
    query = db.query(Warranty)
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination, WarrantyResponse)

@router.get("/warranties/product/{product_id}", response_model=WarrantyResponse)
def get_product_warranty(
    product_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    warranty = db.query(Warranty).filter(Warranty.product_id == product_id).first()
    if not warranty:
        raise HTTPException(status_code=404, detail="Warranty not found for this product")
    return warranty

@router.patch("/warranties/{warranty_id}", response_model=WarrantyResponse)
def update_warranty(
    warranty_id: int, 
    warranty_data: WarrantyCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    warranty = db.query(Warranty).filter(Warranty.id == warranty_id).first()
    if not warranty:
        raise HTTPException(status_code=404, detail="Warranty not found")
    
    product = db.query(Product).filter(
        and_(Product.id == warranty_data.product_id, Product.active == True)
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    brand = db.query(Brand).filter(
        and_(Brand.id == warranty_data.brand_id, Brand.active == True)
    ).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    try:
        with db.begin_nested():
            for key, value in warranty_data.model_dump().items():
                setattr(warranty, key, value)
            db.flush()
        db.commit()
        return warranty
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/warranties/{warranty_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warranty(
    warranty_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    warranty = db.query(Warranty).filter(Warranty.id == warranty_id).first()
    if not warranty:
        raise HTTPException(status_code=404, detail="Warranty not found")
    
    try:
        with db.begin_nested():
            db.delete(warranty)
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
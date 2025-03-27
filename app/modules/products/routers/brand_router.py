from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.products.models import Brand
from app.modules.products.schemas.brand_schema import BrandCreate, BrandResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate

router = APIRouter(prefix="/products", tags=["products"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/brands", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
def create_brand(brand_data: BrandCreate, db: Session = Depends(get_db)):
    existing = db.query(Brand).filter(Brand.name == brand_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Brand with this name already exists")
    
    try:
        with db.begin_nested():
            brand = Brand(**brand_data.model_dump(), active=True)
            db.add(brand)
            db.flush()
        db.commit()
        return brand
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/brands", response_model=PagedResponse[BrandResponse])
def get_brands(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc")
):
    query = db.query(Brand).filter(Brand.active == True)
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination)

@router.get("/brands/{brand_id}", response_model=BrandResponse)
def get_brand(brand_id: int, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(
        and_(Brand.id == brand_id, Brand.active == True)
    ).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    return brand

@router.patch("/brands/{brand_id}", response_model=BrandResponse)
def update_brand(brand_id: int, brand_data: BrandCreate, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(
        and_(Brand.id == brand_id, Brand.active == True)
    ).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    if brand_data.name != brand.name:
        existing = db.query(Brand).filter(Brand.name == brand_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Brand with this name already exists")
    
    try:
        with db.begin_nested():
            brand.name = brand_data.name
            if brand_data.warranty_policy is not None:
                brand.warranty_policy = brand_data.warranty_policy
            db.flush()
        db.commit()
        return brand
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand(brand_id: int, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(
        and_(Brand.id == brand_id, Brand.active == True)
    ).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    try:
        with db.begin_nested():
            brand.active = False
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
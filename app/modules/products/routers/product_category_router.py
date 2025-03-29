from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.products.models import ProductCategory
from app.modules.products.schemas.product_category_schema import ProductCategoryCreate, ProductCategoryResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate

router = APIRouter(prefix="/products", tags=["products"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/categories", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(name: str, db: Session = Depends(get_db)):
    existing = db.query(ProductCategory).filter(ProductCategory.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")
    
    try:
        with db.begin_nested():
            category = ProductCategory(name=name, active=True)
            db.add(category)
            db.flush()
        db.commit()
        return category
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/categories", response_model=PagedResponse[ProductCategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc")
):
    query = db.query(ProductCategory).filter(ProductCategory.active == True)
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination, ProductCategoryResponse)

@router.get("/categories/{category_id}", response_model=ProductCategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(ProductCategory).filter(
        and_(ProductCategory.id == category_id, ProductCategory.active == True)
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category

@router.patch("/categories/{category_id}", response_model=ProductCategoryResponse)
def update_category(category_id: int, name: str, db: Session = Depends(get_db)):
    category = db.query(ProductCategory).filter(
        and_(ProductCategory.id == category_id, ProductCategory.active == True)
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if name != category.name:
        existing = db.query(ProductCategory).filter(ProductCategory.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category with this name already exists")
    
    try:
        with db.begin_nested():
            category.name = name
            db.flush()
        db.commit()
        return category
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(ProductCategory).filter(
        and_(ProductCategory.id == category_id, ProductCategory.active == True)
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    try:
        with db.begin_nested():
            category.active = False
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
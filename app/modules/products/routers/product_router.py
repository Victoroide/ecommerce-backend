from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
from app.core.db import SessionLocal
from app.modules.products.models import Product, Brand
from app.modules.products.schemas.product_schema import ProductCreate, ProductResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate
from app.modules.authentication.dependencies import get_current_user, get_admin_user
from app.modules.authentication.models.user import User

router = APIRouter(prefix="/products", tags=["products"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    brand = db.query(Brand).filter(
        and_(Brand.id == product_data.brand_id, Brand.active == True)
    ).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    try:
        with db.begin_nested():
            product = Product(**product_data.model_dump(), active=True)
            db.add(product)
            db.flush()
        db.commit()
        return product
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/", response_model=PagedResponse[ProductResponse])
def get_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc"),
    brand_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    query = db.query(Product).filter(Product.active == True)
    
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    
    if category:
        query = query.filter(Product.category == category)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Product.name.ilike(search_term) | Product.description.ilike(search_term)
        )
    
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination, ProductResponse)

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(
        and_(Product.id == product_id, Product.active == True)
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product

@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, 
    product_data: ProductCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(
        and_(Product.id == product_id, Product.active == True)
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product_data.brand_id != product.brand_id:
        brand = db.query(Brand).filter(
            and_(Brand.id == product_data.brand_id, Brand.active == True)
        ).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
    
    try:
        with db.begin_nested():
            update_data = product_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(product, key, value)
            db.flush()
        db.commit()
        return product
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(
        and_(Product.id == product_id, Product.active == True)
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    try:
        with db.begin_nested():
            product.active = False
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
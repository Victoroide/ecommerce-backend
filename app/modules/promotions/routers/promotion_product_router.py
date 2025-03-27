from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.core.db import SessionLocal
from app.modules.promotions.models import Promotion, PromotionProduct
from app.modules.promotions.schemas.promotion_schema import PromotionResponse
from app.modules.products.models.product import Product
from app.modules.products.schemas.product_schema import ProductResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate

router = APIRouter(prefix="/promotions", tags=["promotions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{promotion_id}/products/{product_id}", status_code=status.HTTP_201_CREATED)
def add_product_to_promotion(promotion_id: int, product_id: int, db: Session = Depends(get_db)):
    promotion = db.query(Promotion).filter(
        and_(Promotion.id == promotion_id, Promotion.active == True)
    ).first()
    
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found or inactive.")
    
    product = db.query(Product).filter(
        and_(Product.id == product_id, Product.active == True)
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive.")
    
    existing = db.query(PromotionProduct).filter(
        and_(
            PromotionProduct.promotion_id == promotion_id,
            PromotionProduct.product_id == product_id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Product is already in this promotion.")
    
    try:
        with db.begin_nested():
            promo_product = PromotionProduct(
                promotion_id=promotion_id,
                product_id=product_id
            )
            db.add(promo_product)
            db.flush()
        db.commit()
        return {"promotion_id": promotion_id, "product_id": product_id}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{promotion_id}/products", response_model=PagedResponse[ProductResponse])
def get_promotion_products(
    promotion_id: int, 
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc")
):
    promotion = db.query(Promotion).filter(
        and_(Promotion.id == promotion_id, Promotion.active == True)
    ).first()
    
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found or inactive.")
    
    promo_products = db.query(PromotionProduct).filter(
        PromotionProduct.promotion_id == promotion_id
    ).all()
    
    product_ids = [pp.product_id for pp in promo_products]
    
    if not product_ids:
        return PagedResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            pages=0,
            has_next=False,
            has_prev=False
        )
    
    query = db.query(Product).filter(
        and_(Product.id.in_(product_ids), Product.active == True)
    )
    
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination)

@router.delete("/{promotion_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_product_from_promotion(promotion_id: int, product_id: int, db: Session = Depends(get_db)):
    promo_product = db.query(PromotionProduct).filter(
        and_(
            PromotionProduct.promotion_id == promotion_id,
            PromotionProduct.product_id == product_id
        )
    ).first()
    
    if not promo_product:
        raise HTTPException(status_code=404, detail="Product not found in this promotion.")
    
    try:
        with db.begin_nested():
            db.delete(promo_product)
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/products/{product_id}", response_model=PagedResponse[PromotionResponse])
def get_product_promotions(
    product_id: int, 
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query("start_date"),
    sort_order: str = Query("desc"),
    active_only: bool = Query(True)
):
    product = db.query(Product).filter(
        and_(Product.id == product_id, Product.active == True)
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive.")
    
    promo_products = db.query(PromotionProduct).filter(
        PromotionProduct.product_id == product_id
    ).all()
    
    promotion_ids = [pp.promotion_id for pp in promo_products]
    
    if not promotion_ids:
        return PagedResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            pages=0,
            has_next=False,
            has_prev=False
        )
    
    query = db.query(Promotion).filter(Promotion.id.in_(promotion_ids))
    
    if active_only:
        query = query.filter(Promotion.active == True)
    
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from datetime import date
from app.core.db import SessionLocal
from app.modules.authentication.models.user import User
from app.modules.promotions.models.promotion import Promotion
from app.modules.promotions.schemas.promotion_schema import PromotionCreate, PromotionResponse
from app.core.pagination import PaginationParams, PagedResponse, paginate
from app.modules.authentication.dependencies import get_current_user, get_admin_user

router = APIRouter(prefix="/promotions", tags=["promotions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED)
def create_promotion(
    promo_data: PromotionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    try:
        with db.begin_nested():
            promotion = Promotion(
                title=promo_data.title,
                description=promo_data.description,
                discount_percentage=promo_data.discount_percentage,
                start_date=promo_data.start_date,
                end_date=promo_data.end_date,
                active=True
            )
            db.add(promotion)
            db.flush()
        db.commit()
        return promotion
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/", response_model=PagedResponse[PromotionResponse])
def get_promotions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc"),
    active_only: bool = Query(True),
    current_only: bool = Query(False),
    title_search: Optional[str] = Query(None)
):
    query = db.query(Promotion)
    
    if active_only:
        query = query.filter(Promotion.active == True)
    
    if current_only:
        today = date.today()
        query = query.filter(
            and_(
                Promotion.start_date <= today,
                Promotion.end_date >= today
            )
        )
    
    if title_search:
        query = query.filter(Promotion.title.ilike(f"%{title_search}%"))
    
    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination, PromotionResponse)

@router.get("/{promotion_id}", response_model=PromotionResponse)
def get_promotion(
    promotion_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    promotion = db.query(Promotion).filter(
        and_(Promotion.id == promotion_id, Promotion.active == True)
    ).first()
    
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found.")
    
    return promotion

@router.patch("/{promotion_id}", response_model=PromotionResponse)
def update_promotion(
    promotion_id: int, 
    promo_data: PromotionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    promotion = db.query(Promotion).filter(
        and_(Promotion.id == promotion_id, Promotion.active == True)
    ).first()
    
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found.")
    
    try:
        with db.begin_nested():
            update_data = promo_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(promotion, key, value)
            
            db.flush()
        db.commit()
        return promotion
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/{promotion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_promotion(
    promotion_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    promotion = db.query(Promotion).filter(
        and_(Promotion.id == promotion_id, Promotion.active == True)
    ).first()
    
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found.")
    
    try:
        with db.begin_nested():
            promotion.active = False
            db.flush()
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
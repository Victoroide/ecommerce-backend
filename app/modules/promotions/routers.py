from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.modules.promotions.models import Promotion
from app.modules.promotions.schemas import PromotionCreate, PromotionResponse

router = APIRouter(prefix="/promotions", tags=["promotions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=PromotionResponse)
def create_promotion(promo_data: PromotionCreate, db: Session = Depends(get_db)):
    promotion = Promotion(**promo_data.model_dump())
    db.add(promotion)
    db.commit()
    db.refresh(promotion)
    return promotion

@router.get("/", response_model=list[PromotionResponse])
def list_promotions(db: Session = Depends(get_db)):
    return db.query(Promotion).all()

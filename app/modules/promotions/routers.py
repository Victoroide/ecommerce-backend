from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import SessionLocal
from app.modules.promotions.models import Promotion, PromotionProduct
from app.modules.promotions.schemas import PromotionCreate, PromotionResponse

router = APIRouter(prefix="/promotions", tags=["promotions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Promotion CRUD ---

@router.post("/", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED)
def create_promotion(promo_data: PromotionCreate, db: Session = Depends(get_db)):
    promotion = Promotion(
        title=promo_data.title,
        description=promo_data.description,
        discount_percentage=promo_data.discount_percentage,
        start_date=promo_data.start_date,
        end_date=promo_data.end_date,
        active=True
    )
    db.add(promotion)
    db.commit()
    db.refresh(promotion)
    return promotion

@router.get("/", response_model=List[PromotionResponse])
def get_promotions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    promotions = db.query(Promotion).filter(Promotion.active == True).offset(skip).limit(limit).all()
    return promotions

@router.get("/{promotion_id}", response_model=PromotionResponse)
def get_promotion(promotion_id: int, db: Session = Depends(get_db)):
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id, Promotion.active == True).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found.")
    return promotion

@router.patch("/{promotion_id}", response_model=PromotionResponse)
def update_promotion(promotion_id: int, promo_data: PromotionCreate, db: Session = Depends(get_db)):
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id, Promotion.active == True).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found.")
    
    update_data = promo_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(promotion, key, value)
    
    db.commit()
    db.refresh(promotion)
    return promotion

@router.delete("/{promotion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_promotion(promotion_id: int, db: Session = Depends(get_db)):
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id, Promotion.active == True).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found.")
    
    promotion.active = False
    db.commit()
    return None

# --- Promotion Products CRUD ---

@router.post("/{promotion_id}/products/{product_id}", status_code=status.HTTP_201_CREATED)
def add_product_to_promotion(promotion_id: int, product_id: int, db: Session = Depends(get_db)):
    promotion = db.query(Promotion).filter(
        Promotion.id == promotion_id, 
        Promotion.active == True
    ).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found or inactive.")
    
    product = db.query("Product").filter("Product.id" == product_id, "Product.active" == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive.")
    
    existing = db.query(PromotionProduct).filter(
        PromotionProduct.promotion_id == promotion_id,
        PromotionProduct.product_id == product_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Product is already in this promotion.")
    
    promo_product = PromotionProduct(
        promotion_id=promotion_id,
        product_id=product_id
    )
    
    db.add(promo_product)
    db.commit()
    db.refresh(promo_product)
    return {"promotion_id": promotion_id, "product_id": product_id}

@router.get("/{promotion_id}/products")
def get_promotion_products(promotion_id: int, db: Session = Depends(get_db)):
    promotion = db.query(Promotion).filter(
        Promotion.id == promotion_id, 
        Promotion.active == True
    ).first()
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found or inactive.")
    
    promo_products = db.query(PromotionProduct).filter(
        PromotionProduct.promotion_id == promotion_id
    ).all()
    
    product_ids = [pp.product_id for pp in promo_products]
    products = db.query("Product").filter("Product.id".in_(product_ids), "Product.active" == True).all()
    
    return products

@router.delete("/{promotion_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_product_from_promotion(promotion_id: int, product_id: int, db: Session = Depends(get_db)):
    promo_product = db.query(PromotionProduct).filter(
        PromotionProduct.promotion_id == promotion_id,
        PromotionProduct.product_id == product_id
    ).first()
    
    if not promo_product:
        raise HTTPException(status_code=404, detail="Product not found in this promotion.")
    
    db.delete(promo_product)
    db.commit()
    return None

@router.get("/products/{product_id}")
def get_product_promotions(product_id: int, db: Session = Depends(get_db)):
    product = db.query("Product").filter("Product.id" == product_id, "Product.active" == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive.")
    
    promo_products = db.query(PromotionProduct).filter(
        PromotionProduct.product_id == product_id
    ).all()
    
    promotion_ids = [pp.promotion_id for pp in promo_products]
    
    promotions = db.query(Promotion).filter(
        Promotion.id.in_(promotion_ids),
        Promotion.active == True
    ).all()
    
    return promotions
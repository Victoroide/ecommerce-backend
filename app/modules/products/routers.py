from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.modules.products.models import Brand, Product, Inventory, Warranty
from app.modules.products.schemas import BrandCreate, BrandResponse, ProductCreate, ProductResponse, InventoryCreate, InventoryResponse, WarrantyCreate, WarrantyResponse

router = APIRouter(prefix="/products", tags=["products"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints for brands
@router.post("/brands", response_model=BrandResponse)
def create_brand(brand_data: BrandCreate, db: Session = Depends(get_db)):
    brand = Brand(**brand_data.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand

# Endpoints for products
@router.post("/", response_model=ProductResponse)
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

# Endpoints for inventory
@router.post("/inventory", response_model=InventoryResponse)
def create_inventory(inv_data: InventoryCreate, db: Session = Depends(get_db)):
    # Assume price_bs is computed later by a scheduled service
    inventory = Inventory(**inv_data.model_dump(), price_bs=inv_data.price_usd)
    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    return inventory

# Endpoints for warranties
@router.post("/warranties", response_model=WarrantyResponse)
def create_warranty(warranty_data: WarrantyCreate, db: Session = Depends(get_db)):
    warranty = Warranty(**warranty_data.model_dump())
    db.add(warranty)
    db.commit()
    db.refresh(warranty)
    return warranty

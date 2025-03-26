from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import SessionLocal
from app.modules.products.models import *
from app.modules.products.schemas import *

router = APIRouter(prefix="/products", tags=["products"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Brand CRUD ---

@router.post("/brands", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
def create_brand(brand_data: BrandCreate, db: Session = Depends(get_db)):
    existing = db.query(Brand).filter(Brand.name == brand_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Brand with this name already exists.")
    
    brand = Brand(**brand_data.model_dump(), active=True)
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand

@router.get("/brands", response_model=List[BrandResponse])
def get_brands(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    brands = db.query(Brand).filter(Brand.active == True).offset(skip).limit(limit).all()
    return brands

@router.get("/brands/{brand_id}", response_model=BrandResponse)
def get_brand(brand_id: int, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id, Brand.active == True).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found.")
    return brand

@router.patch("/brands/{brand_id}", response_model=BrandResponse)
def update_brand(brand_id: int, brand_data: BrandCreate, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id, Brand.active == True).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found.")
    
    if brand_data.name != brand.name:
        existing = db.query(Brand).filter(Brand.name == brand_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Brand with this name already exists.")
    
    brand.name = brand_data.name
    if brand_data.warranty_policy is not None:
        brand.warranty_policy = brand_data.warranty_policy
    
    db.commit()
    db.refresh(brand)
    return brand

@router.delete("/brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brand(brand_id: int, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id, Brand.active == True).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found.")
    
    brand.active = False
    db.commit()
    return None

# --- Product CRUD ---

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == product_data.brand_id, Brand.active == True).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found.")
    
    product = Product(**product_data.model_dump(), active=True)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.get("/", response_model=List[ProductResponse])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.active == True).offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product

@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product_data: ProductCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    
    if product_data.brand_id is not None and product_data.brand_id != product.brand_id:
        brand = db.query(Brand).filter(Brand.id == product_data.brand_id, Brand.active == True).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found.")
    
    update_data = product_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    
    product.active = False
    db.commit()
    return None

# --- Inventory CRUD ---

@router.post("/inventory", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory(inv_data: InventoryCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == inv_data.product_id, Product.active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    
    existing = db.query(Inventory).filter(Inventory.product_id == inv_data.product_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Inventory already exists for this product.")
    
    inventory = Inventory(**inv_data.model_dump(), price_bs=inv_data.price_usd)
    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    return inventory

@router.get("/inventory", response_model=List[InventoryResponse])
def get_inventories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    inventories = db.query(Inventory).offset(skip).limit(limit).all()
    return inventories

@router.get("/inventory/{product_id}", response_model=InventoryResponse)
def get_product_inventory(product_id: int, db: Session = Depends(get_db)):
    inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found for this product.")
    return inventory

@router.patch("/inventory/{inventory_id}", response_model=InventoryResponse)
def update_inventory(inventory_id: int, stock: int = None, price_usd: float = None, db: Session = Depends(get_db)):
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found.")
    
    if stock is not None:
        if stock < 0:
            raise HTTPException(status_code=400, detail="Stock cannot be negative.")
        inventory.stock = stock
    
    if price_usd is not None:
        if price_usd <= 0:
            raise HTTPException(status_code=400, detail="Price must be greater than zero.")
        inventory.price_usd = price_usd
        # In a real app, price_bs would be calculated based on exchange rate
        # For simplicity, we'll keep them in sync for now
        inventory.price_bs = price_usd
    
    db.commit()
    db.refresh(inventory)
    return inventory

@router.delete("/inventory/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory(inventory_id: int, db: Session = Depends(get_db)):
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found.")
    
    db.delete(inventory)
    db.commit()
    return None

# --- Warranty CRUD ---

@router.post("/warranties", response_model=WarrantyResponse, status_code=status.HTTP_201_CREATED)
def create_warranty(warranty_data: WarrantyCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == warranty_data.product_id, Product.active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    
    brand = db.query(Brand).filter(Brand.id == warranty_data.brand_id, Brand.active == True).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found.")
    
    existing = db.query(Warranty).filter(Warranty.product_id == warranty_data.product_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Warranty already exists for this product.")
    
    warranty = Warranty(**warranty_data.model_dump())
    db.add(warranty)
    db.commit()
    db.refresh(warranty)
    return warranty

@router.get("/warranties", response_model=List[WarrantyResponse])
def get_warranties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    warranties = db.query(Warranty).offset(skip).limit(limit).all()
    return warranties

@router.get("/warranties/product/{product_id}", response_model=WarrantyResponse)
def get_product_warranty(product_id: int, db: Session = Depends(get_db)):
    warranty = db.query(Warranty).filter(Warranty.product_id == product_id).first()
    if not warranty:
        raise HTTPException(status_code=404, detail="Warranty not found for this product.")
    return warranty

@router.patch("/warranties/{warranty_id}", response_model=WarrantyResponse)
def update_warranty(warranty_id: int, warranty_data: WarrantyCreate, db: Session = Depends(get_db)):
    warranty = db.query(Warranty).filter(Warranty.id == warranty_id).first()
    if not warranty:
        raise HTTPException(status_code=404, detail="Warranty not found.")
    
    if warranty_data.product_id != warranty.product_id:
        product = db.query(Product).filter(Product.id == warranty_data.product_id, Product.active == True).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
    
    if warranty_data.brand_id != warranty.brand_id:
        brand = db.query(Brand).filter(Brand.id == warranty_data.brand_id, Brand.active == True).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found.")
    
    for key, value in warranty_data.model_dump().items():
        setattr(warranty, key, value)
    
    db.commit()
    db.refresh(warranty)
    return warranty

@router.delete("/warranties/{warranty_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warranty(warranty_id: int, db: Session = Depends(get_db)):
    warranty = db.query(Warranty).filter(Warranty.id == warranty_id).first()
    if not warranty:
        raise HTTPException(status_code=404, detail="Warranty not found.")
    
    db.delete(warranty)
    db.commit()
    return None

# --- Category CRUD ---

@router.post("/categories", response_model=ProductCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(name: str, db: Session = Depends(get_db)):
    existing = db.query(ProductCategory).filter(ProductCategory.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists.")
    
    category = ProductCategory(name=name, active=True)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@router.get("/categories", response_model=List[ProductCategoryResponse])
def get_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categories = db.query(ProductCategory).filter(ProductCategory.active == True).offset(skip).limit(limit).all()
    return categories

@router.get("/categories/{category_id}", response_model=ProductCategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(ProductCategory).filter(ProductCategory.id == category_id, ProductCategory.active == True).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    return category

@router.patch("/categories/{category_id}", response_model=ProductCategoryResponse)
def update_category(category_id: int, name: str, db: Session = Depends(get_db)):
    category = db.query(ProductCategory).filter(ProductCategory.id == category_id, ProductCategory.active == True).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    
    if name != category.name:
        existing = db.query(ProductCategory).filter(ProductCategory.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category with this name already exists.")
    
    category.name = name
    db.commit()
    db.refresh(category)
    return category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(ProductCategory).filter(ProductCategory.id == category_id, ProductCategory.active == True).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    
    category.active = False
    db.commit()
    return None
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
import json
import logging
from app.core.db import SessionLocal
from app.modules.products.models import Product, Brand
from app.modules.products.schemas.product_schema import (
    ProductCreate, ProductResponse, ProductUpdate,
    BulkProductCreate, BulkProductResponse
)
from app.core.pagination import PaginationParams, PagedResponse, paginate
from app.modules.authentication.dependencies import get_current_user, get_admin_user
from app.modules.authentication.models.user import User
from app.core.file_utils import upload_product_image, upload_product_model_3d, upload_ar_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: str = Form(...),
    image: Optional[UploadFile] = File(None),
    model_3d: Optional[UploadFile] = File(None),
    ar_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    try:
        product_data = json.loads(data)
        brand_id = product_data.get("brand_id")
        brand = db.query(Brand).filter(and_(Brand.id == brand_id, Brand.active == True)).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")

        with db.begin_nested():
            product = Product(**product_data, active=True)
            db.add(product)
            db.flush()
            product_id = product.id

            if image:
                product.image_url = await upload_product_image(image, product_id)

            if model_3d:
                product.model_3d_url = await upload_product_model_3d(model_3d, product_id)

            if ar_file:
                product.ar_url = await upload_ar_file(ar_file, product_id)

            db.flush()
        db.commit()
        logger.info(f"Product created successfully: ID={product.id}, Name={product.name}")
        return product
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.post("/bulk", response_model=BulkProductResponse, status_code=status.HTTP_201_CREATED)
def create_products_bulk(
    bulk_data: BulkProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    products_data = bulk_data.products
    if not products_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No products provided"
        )

    created_products = []
    try:
        with db.begin_nested():
            for product_item in products_data:
                brand_id = product_item.brand_id
                brand = db.query(Brand).filter(and_(Brand.id == brand_id, Brand.active == True)).first()
                if not brand:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Brand with ID {brand_id} not found or inactive"
                    )

                product_dict = product_item.model_dump()
                product = Product(**product_dict, active=True)
                db.add(product)
                db.flush()
                created_products.append(product)
        db.commit()
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating products in bulk: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating products in bulk: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

    return {
        "message": f"Successfully created {len(created_products)} products",
        "products": created_products
    }

@router.get("/", response_model=PagedResponse[ProductResponse])
def get_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc"),
    brand_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None)
):
    query = db.query(Product).filter(Product.active == True)

    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        term = f"%{search}%"
        query = query.filter(Product.name.ilike(term) | Product.description.ilike(term))

    pagination = PaginationParams(page, page_size, sort_by, sort_order)
    return paginate(query, pagination, ProductResponse)

@router.get("/{product_id:int}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(and_(Product.id == product_id, Product.active == True)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.patch("/{product_id:int}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    model_3d: Optional[UploadFile] = File(None),
    ar_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(and_(Product.id == product_id, Product.active == True)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        with db.begin_nested():
            if data:
                try:
                    product_data = json.loads(data)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid JSON data")

                if "brand_id" in product_data and product_data["brand_id"] != product.brand_id:
                    brand = db.query(Brand).filter(and_(Brand.id == product_data["brand_id"], Brand.active == True)).first()
                    if not brand:
                        raise HTTPException(status_code=404, detail="Brand not found")

                for key, value in product_data.items():
                    setattr(product, key, value)

            if image:
                product.image_url = await upload_product_image(image, product_id)
            if model_3d:
                product.model_3d_url = await upload_product_model_3d(model_3d, product_id)
            if ar_file:
                product.ar_url = await upload_ar_file(ar_file, product_id)

            db.flush()
        db.commit()
        logger.info(f"Product updated successfully: ID={product.id}, Name={product.name}")
        return product
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.delete("/{product_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(and_(Product.id == product_id, Product.active == True)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        with db.begin_nested():
            product.active = False
            db.flush()
        db.commit()
        logger.info(f"Product deleted (marked inactive): ID={product.id}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

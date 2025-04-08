from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Body
from typing import Optional, List
from sqlalchemy.orm import Session
import json
import logging

from app.core.db import SessionLocal
from app.modules.products.models import Product, Brand, ProductCategory
from app.modules.products.schemas.product_schema import *
from app.core.pagination import PaginationParams, PagedResponse, paginate
from app.modules.authentication.dependencies import get_current_user, get_admin_user
from app.modules.authentication.models.user import User
from app.core.file_utils import upload_product_image, upload_product_model_3d, upload_ar_file
from app.services.ml.openai_service import OpenAIService
from app.services.ml.pinecone_service import PineconeService
from app.services.ml.recommendation_service import RecommendationService


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
    product_data: ProductFormSchema = Depends(ProductFormSchema.as_form),
    image: Optional[UploadFile] = File(None),
    model_3d: Optional[UploadFile] = File(None),
    ar_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    try:
        brand = db.query(Brand).filter(Brand.id == product_data.brand_id, Brand.active == True).first()
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")

        category = None
        if product_data.category_id:
            category = db.query(ProductCategory).filter(ProductCategory.id == product_data.category_id).first()

        with db.begin_nested():
            product = Product(**product_data.model_dump(), active=True)
            db.add(product)
            db.flush()

            if image:
                product.image_url = await upload_product_image(image, product.id)
            if model_3d:
                product.model_3d_url = await upload_product_model_3d(model_3d, product.id)
            if ar_file:
                product.ar_url = await upload_ar_file(ar_file, product.id)

            text_data = f"{product.name or ''} {product.description or ''}"
            embedding_service = OpenAIService()
            pinecone_service = PineconeService()
            embedding_vector = embedding_service.get_embeddings(text_data)
            metadata = {
                "brand": brand.name,
                "category": category.name if category else "",
                "text": text_data,
                "technical_specifications": product.technical_specifications or ""
            }
            pinecone_service.upsert_pinecone_data(vector=embedding_vector, id=product.uuid, metadata=metadata)

            db.flush()

        db.commit()
        return product

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/bulk-form", response_model=BulkProductResponse, status_code=status.HTTP_201_CREATED)
async def create_products_bulk_form(
    products: List[ProductMultipartCreate] = Depends(ProductMultipartCreate.as_form),
    images: Optional[List[UploadFile]] = File(None),
    models_3d: Optional[List[UploadFile]] = File(None),
    ar_files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    created_products = []
    embedding_service = OpenAIService()
    pinecone_service = PineconeService()

    try:
        with db.begin_nested():
            for product_data in products:
                brand = db.query(Brand).filter(Brand.id == product_data.brand_id, Brand.active == True).first()
                if not brand:
                    raise HTTPException(status_code=404, detail=f"Brand {product_data.brand_id} not found")

                category = None
                if product_data.category_id:
                    category = db.query(ProductCategory).filter(ProductCategory.id == product_data.category_id).first()

                product = Product(**product_data.model_dump(), active=True)
                db.add(product)
                db.flush()

                i = product_data.index
                if images and len(images) > i:
                    product.image_url = await upload_product_image(images[i], product.id)
                if models_3d and len(models_3d) > i:
                    product.model_3d_url = await upload_product_model_3d(models_3d[i], product.id)
                if ar_files and len(ar_files) > i:
                    product.ar_url = await upload_ar_file(ar_files[i], product.id)

                text_data = f"{product.name or ''} {product.description or ''}"
                vector = embedding_service.get_embeddings(text_data)
                metadata = {
                    "brand": brand.name,
                    "category": category.name if category else "",
                    "text": text_data,
                    "technical_specifications": product.technical_specifications or ""
                }
                pinecone_service.upsert_pinecone_data(vector=vector, id=product.uuid, metadata=metadata)
                created_products.append(product)

        db.commit()

        return {
            "message": f"Successfully created {len(created_products)} products",
            "products": created_products
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/{product_id:int}", response_model=List[ProductResponse])
def get_recommendations_by_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    top_k: int = Query(3, ge=1, le=20),
    brand_filter: Optional[str] = Query(None),
    keywords: Optional[List[str]] = Query(None)
):
    product = db.query(Product).filter(Product.id == product_id, Product.active == True).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    service = RecommendationService(db)
    return service.recommend_products(product, top_k, brand_filter, keywords)

@router.post("/recommendations/search", response_model=List[ProductResponse])
def get_recommendations_by_text(
    input_text: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    top_k: int = Query(3, ge=1, le=20),
    brand_filter: Optional[str] = Query(None),
    keywords: Optional[List[str]] = Query(None)
):
    if not input_text.strip():
        raise HTTPException(status_code=400, detail="Input text is required")

    service = RecommendationService(db)
    return service.recommend_products_by_text(input_text, top_k, brand_filter, keywords)


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
    product = db.query(Product).filter(Product.id == product_id, Product.active == True).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product

@router.patch("/{product_id:int}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductFormPatchSchema = Depends(ProductFormPatchSchema.as_form),
    image: Optional[UploadFile] = File(None),
    model_3d: Optional[UploadFile] = File(None),
    ar_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(Product.id == product_id, Product.active == True).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        with db.begin_nested():
            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            for key, value in update_data.items():
                setattr(product, key, value)

            if image:
                product.image_url = await upload_product_image(image, product.id)

            if model_3d:
                product.model_3d_url = await upload_product_model_3d(model_3d, product.id)

            if ar_file:
                product.ar_url = await upload_ar_file(ar_file, product.id)

            brand = db.query(Brand).filter(Brand.id == product.brand_id).first()
            category = db.query(ProductCategory).filter(ProductCategory.id == product.category_id).first() if product.category_id else None

            text_data = f"{product.name or ''} {product.description or ''}"
            embedding_service = OpenAIService()
            pinecone_service = PineconeService()
            embedding_vector = embedding_service.get_embeddings(text_data)
            metadata = {
                "brand": brand.name if brand else "",
                "category": category.name if category else "",
                "text": text_data,
                "technical_specifications": product.technical_specifications or ""
            }
            pinecone_service.upsert_pinecone_data(vector=embedding_vector, id=product.uuid, metadata=metadata)

            db.flush()

        db.commit()
        return product

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{product_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(Product.id == product_id, Product.active == True).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        with db.begin_nested():
            product.active = False
            db.flush()
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

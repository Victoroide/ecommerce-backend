import os
from typing import List, Optional
from sqlalchemy.orm import Session

from app.modules.products.models import Product
from app.modules.products.schemas.product_schema import ProductResponse
from app.services.ml.pinecone_service import PineconeService
from app.services.ml.openai_service import OpenAIService


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = OpenAIService()
        self.pinecone_service = PineconeService()

    def recommend_products(
        self,
        product: Product,
        top_k: int,
        brand_filter: Optional[str],
        keywords: Optional[List[str]]
    ) -> List[ProductResponse]:
        name_text = product.name or ""
        desc_text = product.description or ""
        combined_text = f"{name_text} {desc_text}"
        vector = self.embedding_service.get_embeddings(combined_text)

        metadata_filter = {}
        if brand_filter:
            metadata_filter = {"brand": {"$eq": brand_filter}}

        keyword_filter = keywords if keywords else None
        response = self.pinecone_service.query_pinecone_data(
            vector=vector,
            top_k=top_k,
            metadata_filter=metadata_filter,
            keyword_filter=keyword_filter
        )

        uuids = [match["id"] for match in response.get("matches", [])]

        if not uuids:
            return []

        products = self.db.query(Product).filter(
            Product.active == True,
            Product.uuid.in_(uuids),
            Product.id != product.id
        ).all()

        results = []
        for p in products:
            result_item = ProductResponse(
                id=p.id,
                uuid=p.uuid,
                brand_id=p.brand_id,
                brand=p.brand,
                category_id=p.category_id,
                category=p.category,
                name=p.name,
                description=p.description,
                active=p.active,
                image_url=p.image_url,
                model_3d_url=p.model_3d_url,
                ar_url=p.ar_url,
                technical_specifications=p.technical_specifications,
                warranty=p.warranty
            )
            results.append(result_item)

        return results

    def recommend_products_by_text(
        self,
        input_text: str,
        top_k: int,
        brand_filter: Optional[str],
        keywords: Optional[List[str]]
    ) -> List[ProductResponse]:
        vector = self.embedding_service.get_embeddings(input_text)

        metadata_filter = {}
        if brand_filter:
            metadata_filter = {"brand": {"$eq": brand_filter}}

        keyword_filter = keywords if keywords else None
        response = self.pinecone_service.query_pinecone_data(
            vector=vector,
            top_k=top_k,
            metadata_filter=metadata_filter,
            keyword_filter=keyword_filter
        )

        uuids = [match["id"] for match in response.get("matches", [])]

        if not uuids:
            return []

        products = self.db.query(Product).filter(
            Product.active == True,
            Product.uuid.in_(uuids)
        ).all()

        results = []
        for p in products:
            result_item = ProductResponse(
                id=p.id,
                uuid=p.uuid,
                brand_id=p.brand_id,
                brand=p.brand,
                category_id=p.category_id,
                category=p.category,
                name=p.name,
                description=p.description,
                active=p.active,
                image_url=p.image_url,
                model_3d_url=p.model_3d_url,
                ar_url=p.ar_url,
                technical_specifications=p.technical_specifications,
                warranty=p.warranty
            )
            results.append(result_item)

        return results
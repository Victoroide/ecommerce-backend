from sqlalchemy import Column, Integer, ForeignKey
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class PromotionProduct(Base, TimestampedModel):
    __tablename__ = "promotion_products"

    id = Column(Integer, primary_key=True)
    promotion_id = Column(Integer, ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    promotion = relationship("Promotion", back_populates="promotion_products")

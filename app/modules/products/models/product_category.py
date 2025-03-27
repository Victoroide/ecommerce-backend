from sqlalchemy import Column, Integer, String, Boolean
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class ProductCategory(Base, TimestampedModel):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    products = relationship("Product", back_populates="category")
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base_class import Base
from app.models.timestamped import TimestampedModel
import uuid

class Product(Base, TimestampedModel):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("product_categories.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True, nullable=False)
    image_url = Column(String(500))
    model_3d_url = Column(String(500))
    ar_url = Column(String(500))
    technical_specifications = Column(Text)
    warranty_id = Column(Integer, ForeignKey("warranties.id", ondelete="SET NULL"), nullable=True)

    category = relationship("ProductCategory", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    inventory = relationship("Inventory", back_populates="product", uselist=False)
    warranty = relationship("Warranty", back_populates="products", uselist=False)
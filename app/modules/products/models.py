from sqlalchemy import Column, Integer, String, Text, ForeignKey, Numeric, Boolean, Interval, URL
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

# Brand model (manufacturers)
class Brand(Base, TimestampedModel):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), unique=True, nullable=False)
    warranty_policy = Column(Text)
    active = Column(Boolean, default=True, nullable=False)

    products = relationship("Product", back_populates="brand")

# Product model
class Product(Base, TimestampedModel):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("product_categories.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True, nullable=False)
    image_url = Column(String(500))
    model_3d_url = Column(String(500))
    ar_url = Column(String(500))
    technical_specifications = Column(Text)
    warranty_info = Column(Text)

    category = relationship("ProductCategory", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    inventory = relationship("Inventory", back_populates="product", uselist=False)
    warranty = relationship("Warranty", back_populates="product", uselist=False)

class ProductCategory(Base, TimestampedModel):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    products = relationship("Product", back_populates="category")

# Inventory model
class Inventory(Base, TimestampedModel):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    price_usd = Column(Numeric(10,2), nullable=False)
    price_bs = Column(Numeric(10,2), nullable=False)

    product = relationship("Product", back_populates="inventory")

# Warranty model (external, from manufacturer)
class Warranty(Base, TimestampedModel):
    __tablename__ = "warranties"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    warranty_type = Column(String(50), nullable=False)  # "manufacturer"
    details = Column(Text)
    duration = Column(Interval)

    product = relationship("Product", back_populates="warranty")
    brand = relationship("Brand")

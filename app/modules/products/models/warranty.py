from sqlalchemy import Column, Integer, String, Text, ForeignKey, Interval
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

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

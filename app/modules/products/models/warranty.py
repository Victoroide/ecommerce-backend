from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_class import Base
from app.models.timestamped import TimestampedModel

class Warranty(Base, TimestampedModel):
    __tablename__ = "warranties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration_months = Column(Integer, nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)

    brand = relationship("Brand", back_populates="warranties")
    products = relationship("Product", back_populates="warranty")
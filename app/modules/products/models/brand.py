from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base_class import Base
from app.models.timestamped import TimestampedModel

class Brand(Base, TimestampedModel):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), unique=True, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    products = relationship("Product", back_populates="brand")
    warranties = relationship("Warranty", back_populates="brand")
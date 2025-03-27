from sqlalchemy import Column, Integer, String, Text, Boolean
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class Brand(Base, TimestampedModel):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), unique=True, nullable=False)
    warranty_policy = Column(Text)
    active = Column(Boolean, default=True, nullable=False)

    products = relationship("Product", back_populates="brand")
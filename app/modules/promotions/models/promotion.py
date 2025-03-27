from sqlalchemy import Column, Integer, String, Text, Numeric, Date, Boolean, ForeignKey
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class Promotion(Base, TimestampedModel):
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    discount_percentage = Column(Numeric(5,2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    promotion_products = relationship("PromotionProduct", back_populates="promotion", cascade="all, delete-orphan")
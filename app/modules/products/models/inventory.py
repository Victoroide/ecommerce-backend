from sqlalchemy import Column, Integer, ForeignKey, Numeric
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class Inventory(Base, TimestampedModel):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    price_usd = Column(Numeric(10,2), nullable=False)
    price_bs = Column(Numeric(10,2), nullable=False)

    product = relationship("Product", back_populates="inventory")
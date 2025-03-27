from sqlalchemy import Column, Integer, ForeignKey, Boolean
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class ShoppingCart(Base, TimestampedModel):
    __tablename__ = "shopping_carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

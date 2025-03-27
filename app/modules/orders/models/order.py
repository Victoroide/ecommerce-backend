from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Boolean
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class Order(Base, TimestampedModel):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Numeric(10,2), nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False)  # pending, paid, shipped, delivered, cancelled
    payment_method = Column(String(10))          # qr, paypal, stripe
    active = Column(Boolean, default=True, nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", uselist=False, back_populates="order")
    delivery = relationship("Delivery", uselist=False, back_populates="order")
    feedback = relationship("Feedback", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base, TimestampedModel):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10,2), nullable=False)

    order = relationship("Order", back_populates="items")
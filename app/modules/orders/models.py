from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Boolean
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

# Shopping Cart and Cart Items
class ShoppingCart(Base, TimestampedModel):
    __tablename__ = "shopping_carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

class CartItem(Base, TimestampedModel):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("shopping_carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    cart = relationship("ShoppingCart", back_populates="items")

# Orders and Order Items
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

# Payment
class Payment(Base, TimestampedModel):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    method = Column(String(10), nullable=False)   # qr, paypal, stripe
    status = Column(String(20), nullable=False)     # initiated, completed, failed
    transaction_id = Column(String(255))

    order = relationship("Order", back_populates="payment")

# Delivery
class Delivery(Base, TimestampedModel):
    __tablename__ = "deliveries"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    delivery_address = Column(String, nullable=False)
    delivery_status = Column(String(20), nullable=False)  # pending, in_transit, delivered, cancelled
    tracking_info = Column(String)
    estimated_arrival = Column(String)

    order = relationship("Order", back_populates="delivery")

# Feedback
class Feedback(Base, TimestampedModel):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String)

    order = relationship("Order", back_populates="feedback")

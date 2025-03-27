from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class Payment(Base, TimestampedModel):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    method = Column(String(10), nullable=False)   # qr, paypal, stripe
    status = Column(String(20), nullable=False)     # initiated, completed, failed
    transaction_id = Column(String(255))

    order = relationship("Order", back_populates="payment")
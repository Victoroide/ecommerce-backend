from sqlalchemy import Column, Integer, String, ForeignKey
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class Delivery(Base, TimestampedModel):
    __tablename__ = "deliveries"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    delivery_address = Column(String, nullable=False)
    delivery_status = Column(String(20), nullable=False)  # pending, in_transit, delivered, cancelled
    tracking_info = Column(String)
    estimated_arrival = Column(String)

    order = relationship("Order", back_populates="delivery")
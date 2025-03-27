from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class ChatbotSession(Base, TimestampedModel):
    __tablename__ = "chatbot_sessions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_token = Column(String(255), unique=True, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    messages = relationship("ChatbotMessage", back_populates="session", cascade="all, delete-orphan")

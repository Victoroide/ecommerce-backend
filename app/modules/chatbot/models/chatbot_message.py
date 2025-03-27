from sqlalchemy import Column, Integer, String, ForeignKey, Text
from app.models.timestamped import TimestampedModel
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class ChatbotMessage(Base, TimestampedModel):
    __tablename__ = "chatbot_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chatbot_sessions.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(5), nullable=False)  # "user" or "bot"
    message = Column(Text, nullable=False)

    session = relationship("ChatbotSession", back_populates="messages")

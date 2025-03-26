from sqlalchemy import Column, Integer, String, Boolean
from app.models.timestamped import TimestampedModel
from app.models.base_class import Base

class User(Base, TimestampedModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    first_name = Column(String(40))
    last_name = Column(String(40))
    role = Column(String(10), nullable=False)  # "admin", "customer"
    active = Column(Boolean, default=True, nullable=False)

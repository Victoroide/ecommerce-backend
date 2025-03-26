from sqlalchemy import Column, DateTime
from app.models.base_class import Base
from datetime import datetime

class TimestampedModel:
    __abstract__ = True
    
    created_at = Column(DateTime, default=datetime.now(), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now(), nullable=False)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base_class import Base
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from app.modules.authentication.models.user import User
    from app.modules.products.models import Brand, Product, Inventory, Warranty, ProductCategory
    from app.modules.orders.models import Order, OrderItem, Feedback, Payment, ShoppingCart, CartItem
    from app.modules.chatbot.models import ChatbotMessage, ChatbotSession
    from app.modules.promotions.models import Promotion, PromotionProduct
    Base.metadata.create_all(bind=engine)

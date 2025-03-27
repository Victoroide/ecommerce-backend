from app.modules.promotions.routers.promotion_router import router as promotion_router
from app.modules.promotions.routers.promotion_product_router import router as promotion_product_router

promotions = (promotion_router, promotion_product_router)
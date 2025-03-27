from app.modules.orders.routers.delivery_router import router as delivery_router
from app.modules.orders.routers.order_router import router as order_router
from app.modules.orders.routers.payment_router import router as payment_router
from app.modules.orders.routers.shopping_cart_router import router as shopping_cart_router
from app.modules.orders.routers.shopping_cart_item_router import router as shopping_cart_item_router
from app.modules.orders.routers.feedback_router import router as feedback_router

orders = (delivery_router, order_router, payment_router, shopping_cart_router, shopping_cart_item_router, feedback_router)
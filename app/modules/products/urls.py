from app.modules.products.routers.brand_router import router as brand_router
from app.modules.products.routers.product_router import router as product_router
from app.modules.products.routers.warranty_router import router as warranty_router
from app.modules.products.routers.product_category_router import router as product_category_router
from app.modules.products.routers.inventory_router import router as inventory_router

products = (brand_router, product_router, warranty_router, product_category_router, inventory_router)
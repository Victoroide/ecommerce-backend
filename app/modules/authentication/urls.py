from app.modules.authentication.routers.user_router import router as user_router
from app.modules.authentication.routers.auth_router import router as auth_router

authentication = [user_router, auth_router]
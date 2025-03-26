from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.authentication.routers import router as authentication
from app.modules.chatbot.routers import router as chatbot
from app.modules.orders.routers import router as orders
from app.modules.products.routers import router as products
from app.modules.promotions.routers import router as promotions

app = FastAPI(title="E-commerce Backend", version="1.0.0")

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authentication)
app.include_router(products)
app.include_router(orders)
app.include_router(promotions)
app.include_router(chatbot)

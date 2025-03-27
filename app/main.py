from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.authentication.urls import authentication
from app.modules.chatbot.urls import chatbot
from app.modules.orders.urls import orders
from app.modules.products.urls import products
from app.modules.promotions.urls import promotions

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
app.include_router(chatbot)
app.include_router(products)
app.include_router(orders)
app.include_router(promotions)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.authentication.urls import authentication
from app.modules.chatbot.urls import chatbot
from app.modules.orders.urls import orders
from app.modules.products.urls import products
from app.modules.promotions.urls import promotions

app = FastAPI(title="E-commerce Backend", version="1.0.0")

origins = [
    "http://localhost:4200",
    "http://localhost:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in authentication:
    app.include_router(router)

for router in chatbot:
    app.include_router(router)

for router in products:
    app.include_router(router)
    
for router in orders:
    app.include_router(router)
    
for router in promotions:
    app.include_router(router)
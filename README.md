# E-commerce Backend

This is the backend for an e-commerce system for appliances with AR visualization, dynamic inventory updates, secure payments (QR & international), integrated chatbot (OpenAI‑4), and more.

## Features

- Modular FastAPI backend with SQLAlchemy and Alembic migrations.
- Dockerized deployment.
- RESTful endpoints for authentication, products, orders, promotions, and chatbot.
- Scheduled inventory price updates via Binance API (handled in a service).

## Setup

1. Update `.env` with your database URL and OpenAI API key.
2. Build and run the containers:
   ```bash
   docker-compose up --build

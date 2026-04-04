"""
Stock Tracker API - Main Application
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import router as api_v1_router
from app.api.v1 import websocket
from app.core.init_db import init_db
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Stock Tracker API starting up...")
    await init_db()
    yield
    logger.info("Stock Tracker API shutting down...")


app = FastAPI(
    title="Stock Tracker API",
    description="""
## Stock Tracker REST API

A comprehensive API for tracking stock prices, managing watchlists, and setting price alerts.

## Authentication

Most endpoints require JWT Bearer token authentication. 
Use the `/api/v1/auth/login` endpoint to obtain a token.

## Rate Limiting

API requests are rate-limited to ensure fair usage:
- Default: 100 requests/minute per API key or IP
- Authenticated users: 100 requests/minute
- Public endpoints: 30 requests/minute

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Time when the limit resets (Unix timestamp)

## API Keys

Generate API keys via the `/api-keys` endpoints for programmatic access.
API keys should be passed in the `Authorization: Bearer <key>` header.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware for frontend-backend separation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Include API v1 routes
app.include_router(api_v1_router)

# WebSocket routes at root level
app.include_router(websocket.router)


@app.get("/")
async def root():
    return {"message": "Stock Tracker API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """
    Health check endpoint for load balancers and monitoring.
    
    Returns:
        Health status with component details.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "stock-tracker-api"
    }

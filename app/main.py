"""
Stock Tracker API - Main Application
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.api.v1 import websocket
from app.core.init_db import init_db

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
    description="API for tracking stock prices, managing watchlists and alerts",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend-backend separation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

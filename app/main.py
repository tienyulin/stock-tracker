"""
Stock Tracker API - Main Application
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Stock Tracker API starting up...")
    yield
    # Shutdown
    print("Stock Tracker API shutting down...")


app = FastAPI(
    title="Stock Tracker API",
    description="API for tracking stock prices, managing watchlists and alerts",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API v1 routes
app.include_router(api_v1_router)


@app.get("/")
async def root():
    return {"message": "Stock Tracker API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

"""
Stock Tracker API - Main Application
"""
from fastapi import FastAPI

app = FastAPI(
    title="Stock Tracker API",
    description="API for tracking stock prices, managing watchlists and alerts",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {"message": "Stock Tracker API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

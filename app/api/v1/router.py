"""
API v1 router.
"""
from fastapi import APIRouter

from app.api.v1 import alerts, stocks, watchlists

router = APIRouter(prefix="/api/v1")

router.include_router(stocks.router)
router.include_router(watchlists.router)
router.include_router(alerts.router)

"""
API v1 router.
"""

from fastapi import APIRouter

from app.api.v1 import alerts, auth, stocks, watchlists, users, portfolio, api_keys, simulation

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(stocks.router)
router.include_router(watchlists.router)
router.include_router(alerts.router)
router.include_router(users.router)
router.include_router(portfolio.router)
router.include_router(api_keys.router)
router.include_router(simulation.router)

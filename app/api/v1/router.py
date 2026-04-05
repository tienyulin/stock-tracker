"""
API v1 router.
"""

from fastapi import APIRouter

from app.api.v1 import alerts, auth, stocks, watchlists, users, portfolio, api_keys, simulation, simulations, tax_report, broker_sync, social, portfolio_health, signals, options, dividends

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(stocks.router)
router.include_router(watchlists.router)
router.include_router(alerts.router)
router.include_router(users.router)
router.include_router(portfolio.router)
router.include_router(api_keys.router)
router.include_router(simulation.router)
router.include_router(simulations.router)
router.include_router(tax_report.router)
router.include_router(broker_sync.router)
router.include_router(social.router)
router.include_router(portfolio_health.router)
router.include_router(signals.router)
router.include_router(options.router)
router.include_router(dividends.router)

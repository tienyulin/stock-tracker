"""
API v1 router.
"""

from fastapi import APIRouter

from app.api.v1 import alerts, auth, stocks, watchlists, users, portfolio, api_keys, simulation, tax_report, broker_sync, social, portfolio_health, signals, options, dividends, portfolio_overview, passive_income, agent, financial_coach, wealth_transfer, cash_flow, tax_optimization, alternative_investments, fixed_income, commodities, esg

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(stocks.router)
router.include_router(watchlists.router)
router.include_router(alerts.router)
router.include_router(users.router)
router.include_router(portfolio.router)
router.include_router(api_keys.router)
router.include_router(simulation.router)
router.include_router(tax_report.router)
router.include_router(broker_sync.router)
router.include_router(social.router)
router.include_router(portfolio_health.router)
router.include_router(signals.router)
router.include_router(options.router)
router.include_router(dividends.router)
router.include_router(portfolio_overview.router)
router.include_router(passive_income.router)
router.include_router(agent.router)
router.include_router(financial_coach.router)
router.include_router(wealth_transfer.router)
router.include_router(cash_flow.router)
router.include_router(tax_optimization.router)
router.include_router(alternative_investments.router)
router.include_router(fixed_income.router)
router.include_router(commodities.router)
router.include_router(esg.router)

"""
Risk Analytics Portfolio API

Provides portfolio risk metrics including VaR, Sharpe Ratio, Max Drawdown.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

import logging

from app.core.database import get_db
from app.models.models import UserHolding
from app.services.risk_analytics_service import RiskAnalyticsService
from app.services.yfinance_service import YFinanceService
from app.utils.auth import decode_access_token

router = APIRouter(prefix="/portfolio/risk-analytics", tags=["portfolio", "risk"])


class RiskAnalyticsResponse(BaseModel):
    """Risk analytics response model."""

    portfolio_value: float
    var_95: float
    var_99: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_percent: float
    vs_sp500_return: float
    sp500_return: float
    portfolio_return: float
    volatility: float
    timestamp: str


class RiskAnalyticsRequest(BaseModel):
    """Optional parameters for risk analytics."""

    lookback_days: Optional[int] = 90  # Default 90 days history


def get_current_user_id(authorization: str = Header(...)) -> str:
    """Extract user ID from authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return user_id


@router.get("", response_model=RiskAnalyticsResponse)
async def get_portfolio_risk_analytics(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    lookback_days: int = 90,
):
    """
    Get portfolio risk analytics.

    Calculates VaR, Sharpe Ratio, Max Drawdown, and vs S&P 500 comparison.

    Args:
        lookback_days: Number of days of historical data to use (default 90).

    Returns:
        RiskMetrics with all risk indicators.
    """
    logger = logging.getLogger(__name__)

    # Get user holdings
    result = await db.execute(
        select(UserHolding).where(UserHolding.user_id == user_id)
    )
    holdings = result.scalars().all()

    if not holdings:
        return RiskAnalyticsResponse(
            portfolio_value=0,
            var_95=0,
            var_99=0,
            sharpe_ratio=0,
            max_drawdown=0,
            max_drawdown_percent=0,
            vs_sp500_return=0,
            sp500_return=0,
            portfolio_return=0,
            volatility=0,
            timestamp="",
        )

    # Prepare holdings data
    holdings_data = [
        {
            "symbol": h.symbol,
            "quantity": h.quantity,
            "avg_cost": h.avg_cost,
        }
        for h in holdings
    ]

    # Get current prices
    yfinance = YFinanceService()
    prices = {}
    symbols = [h.symbol for h in holdings]

    try:
        for symbol in symbols:
            try:
                quote = await yfinance.get_quote(symbol)
                prices[symbol] = quote.price
            except Exception as e:
                logger.warning(f"Failed to get price for {symbol}: {e}")
                prices[symbol] = 0
    finally:
        await yfinance.close()

    # Get historical prices
    historical_prices = {}
    try:
        for symbol in symbols:
            try:
                history = await yfinance.get_historical(
                    symbol=symbol,
                    period=f"{lookback_days}d",
                )
                if history and history.closes:
                    historical_prices[symbol] = history.closes
            except Exception as e:
                logger.warning(f"Failed to get history for {symbol}: {e}")
    finally:
        await yfinance.close()

    # Get S&P 500 historical data (^GSPC)
    sp500_historical = []
    try:
        sp500_history = await yfinance.get_historical(
            symbol="^GSPC",
            period=f"{lookback_days}d",
        )
        if sp500_history and sp500_history.closes:
            sp500_historical = sp500_history.closes
    except Exception as e:
        logger.warning(f"Failed to get S&P 500 history: {e}")

    # Calculate risk metrics
    risk_service = RiskAnalyticsService()
    metrics = await risk_service.calculate_risk_metrics(
        holdings=holdings_data,
        prices=prices,
        historical_prices=historical_prices,
        sp500_historical=sp500_historical,
    )

    return RiskAnalyticsResponse(
        portfolio_value=metrics.portfolio_value,
        var_95=metrics.var_95,
        var_99=metrics.var_99,
        sharpe_ratio=metrics.sharpe_ratio,
        max_drawdown=metrics.max_drawdown,
        max_drawdown_percent=metrics.max_drawdown_percent,
        vs_sp500_return=metrics.vs_sp500_return,
        sp500_return=metrics.sp500_return,
        portfolio_return=metrics.portfolio_return,
        volatility=metrics.volatility,
        timestamp=metrics.timestamp,
    )

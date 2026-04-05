"""
Portfolio Overview Endpoint - Phase 29
Single-pane command center aggregating all portfolio data.
"""

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.models import User
from app.utils.auth import decode_access_token

router = APIRouter(prefix="/portfolio/overview", tags=["portfolio"])

logger = logging.getLogger(__name__)


# Request/Response Models
class AssetAllocation(BaseModel):
    stocks: float
    options: float
    dividends: float


class TopPerformer(BaseModel):
    symbol: str
    change_pct: float
    current_value: float


class UpcomingDividend(BaseModel):
    symbol: str
    ex_dividend_date: str
    payment_date: str
    amount_per_share: float


class AISignalsSummary(BaseModel):
    buy: int
    hold: int
    sell: int


class RecentAlert(BaseModel):
    id: str
    symbol: str
    condition_type: str
    threshold: float
    triggered_at: Optional[str] = None


class OptionsGreeks(BaseModel):
    delta: float
    gamma: float
    theta: float
    vega: float


class PortfolioOverviewResponse(BaseModel):
    total_value: float
    daily_change: float
    daily_change_pct: float
    asset_allocation: AssetAllocation
    top_gainers: list[TopPerformer]
    top_losers: list[TopPerformer]
    upcoming_dividends: list[UpcomingDividend]
    ai_signals_summary: AISignalsSummary
    portfolio_health_score: int
    recent_alerts: list[RecentAlert]
    options_greeks: OptionsGreeks


async def get_current_user_id(authorization: str = Header(None)) -> str:
    """Extract user ID from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return user_id


async def get_current_user(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)) -> User:
    """Get current authenticated user."""
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("", response_model=PortfolioOverviewResponse)
async def get_portfolio_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get unified portfolio overview combining all portfolio data.
    
    Returns:
        - Net worth with daily change
        - Asset allocation breakdown
        - Top gainers/losers
        - Upcoming dividends (30 days)
        - AI signals summary
        - Portfolio health score
        - Recent alerts
        - Options Greeks summary
    """
    # Placeholder - actual implementation aggregates from:
    # - portfolio_service (holdings, values)
    # - dividends_service (upcoming dividends)
    # - signals_service (AI signals)
    # - portfolio_health_service (health score)
    # - options_service (greeks)
    # - alerts_service (recent alerts)
    
    return PortfolioOverviewResponse(
        total_value=0.0,
        daily_change=0.0,
        daily_change_pct=0.0,
        asset_allocation=AssetAllocation(stocks=0.0, options=0.0, dividends=0.0),
        top_gainers=[],
        top_losers=[],
        upcoming_dividends=[],
        ai_signals_summary=AISignalsSummary(buy=0, hold=0, sell=0),
        portfolio_health_score=0,
        recent_alerts=[],
        options_greeks=OptionsGreeks(delta=0.0, gamma=0.0, theta=0.0, vega=0.0),
    )

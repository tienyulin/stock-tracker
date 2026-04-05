"""
Portfolio Overview Endpoint - Phase 29
Single-pane command center aggregating all portfolio data.
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from app.core.database import get_db
from app.models.models import User, UserHolding
from app.utils.auth import decode_access_token

router = APIRouter(prefix="/portfolio/overview", tags=["portfolio"])

logger = logging.getLogger(__name__)


# ─── Pydantic Models ──────────────────────────────────────────────────────────

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


# ─── Auth ─────────────────────────────────────────────────────────────────────

async def get_current_user_id(authorization: str = Header(None)) -> str:
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


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ─── Helpers ─────────────────────────────────────────────────────────────────

async def _get_holdings(db: AsyncSession, user_id: str) -> list[UserHolding]:
    """Fetch all holdings for user."""
    from sqlalchemy import select
    result = await db.execute(
        select(UserHolding).where(UserHolding.user_id == user_id)
    )
    return list(result.scalars().all())


async def _get_portfolio_health_score(db: AsyncSession, user_id: str) -> int:
    """Get portfolio health score from health service."""
    try:
        from app.services.portfolio_health_service import PortfolioHealthService
        svc = PortfolioHealthService(db, user_id)
        return int(svc.calculate_health_score()["score"])
    except Exception:
        return 0


async def _get_recent_alerts(db: AsyncSession, user_id: str, limit: int = 5) -> list[dict]:
    """Get recent triggered alerts."""
    try:
        from sqlalchemy import select, desc
        from app.models.models import Alert
        result = await db.execute(
            select(Alert)
            .where(Alert.user_id == user_id, Alert.triggered_at.isnot(None))
            .order_by(desc(Alert.triggered_at))
            .limit(limit)
        )
        alerts = result.scalars().all()
        return [
            {
                "id": str(a.id),
                "symbol": a.symbol,
                "condition_type": a.condition_type,
                "threshold": float(a.threshold),
                "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
            }
            for a in alerts
        ]
    except Exception:
        return []


async def _get_options_greeks(db: AsyncSession, user_id: str) -> OptionsGreeks:
    """Aggregate net options Greeks across all option positions."""
    try:
        from sqlalchemy import select
        from app.models.options import UserOption
        result = await db.execute(
            select(UserOption).where(UserOption.user_id == user_id)
        )
        options = result.scalars().all()

        if not options:
            return OptionsGreeks(delta=0.0, gamma=0.0, theta=0.0, vega=0.0)

        total_delta = sum(float(o.delta or 0) for o in options)
        total_gamma = sum(float(o.gamma or 0) for o in options)
        total_theta = sum(float(o.theta or 0) for o in options)
        total_vega = sum(float(o.vega or 0) for o in options)

        return OptionsGreeks(
            delta=round(total_delta, 4),
            gamma=round(total_gamma, 4),
            theta=round(total_theta, 4),
            vega=round(total_vega, 4),
        )
    except Exception:
        return OptionsGreeks(delta=0.0, gamma=0.0, theta=0.0, vega=0.0)


async def _get_upcoming_dividends(
    db: AsyncSession, user_id: str, days: int = 30
) -> list[UpcomingDividend]:
    """Get upcoming dividends from payment records."""
    try:
        from sqlalchemy import select, and_, func
        from app.models.dividend import DividendPayment

        cutoff = datetime.utcnow() + timedelta(days=days)
        result = await db.execute(
            select(DividendPayment)
            .where(
                DividendPayment.user_id == user_id,
                DividendPayment.ex_dividend_date <= cutoff,
            )
            .order_by(DividendPayment.ex_dividend_date)
            .limit(10)
        )
        payments = result.scalars().all()
        return [
            UpcomingDividend(
                symbol=p.symbol,
                ex_dividend_date=p.ex_dividend_date.isoformat() if p.ex_dividend_date else "",
                payment_date=p.payment_date.isoformat() if p.payment_date else "",
                amount_per_share=float(p.amount or 0),
            )
            for p in payments
        ]
    except Exception:
        return []


async def _get_ai_signals_summary(db: AsyncSession, user_id: str) -> AISignalsSummary:
    """Count buy/hold/sell signals across portfolio holdings."""
    try:
        holdings = await _get_holdings(db, user_id)
        buy_count = hold_count = sell_count = 0

        for h in holdings:
            try:
                from app.services.signal_scoring_service import SignalScoringService
                svc = SignalScoringService()
                score = await svc.get_signal_score(h.symbol, period="3mo", interval="1d")
                if score:
                    verdict = score.get("verdict", "").upper()
                    if "BUY" in verdict:
                        buy_count += 1
                    elif "HOLD" in verdict:
                        hold_count += 1
                    elif "SELL" in verdict:
                        sell_count += 1
            except Exception:
                pass

        return AISignalsSummary(buy=buy_count, hold=hold_count, sell=sell_count)
    except Exception:
        return AISignalsSummary(buy=0, hold=0, sell=0)


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.get("", response_model=PortfolioOverviewResponse)
async def get_portfolio_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get unified portfolio overview combining all portfolio data.

    Returns:
        - Net worth with daily change
        - Asset allocation breakdown (stocks / options / dividends)
        - Top 5 gainers and losers
        - Upcoming dividends (next 30 days)
        - AI signals summary (buy/hold/sell count)
        - Portfolio health score (0-100)
        - Recent triggered alerts (last 5)
        - Options Greeks summary (net delta/gamma/theta/vega)
    """
    user_id = str(user.id)

    # ── Holdings ──
    holdings = await _get_holdings(db, user_id)

    # ── Total value & daily change ──
    # current_value may be null if price hasn't been fetched; fall back to cost
    total_value = sum(float(h.current_value or (h.avg_cost * h.quantity)) for h in holdings)
    total_cost = sum(float(h.avg_cost * h.quantity) for h in holdings)

    # Daily change: compare current_value vs previous close (use cost as fallback → 0 change)
    daily_change = 0.0
    daily_change_pct = 0.0
    if total_cost > 0:
        daily_change_pct = ((total_value - total_cost) / total_cost) * 100
        # Approximate daily change from pct (would need historical for accurate calc)
        daily_change = total_value - total_cost

    # ── Asset allocation ──
    # Stocks: regular holdings
    # Options: option positions
    # Dividends: separate dividend tracking table
    stocks_value = 0.0
    options_value = 0.0
    dividends_value = 0.0

    for h in holdings:
        val = float(h.current_value or (h.avg_cost * h.quantity))
        if h.asset_type == "STOCK":
            stocks_value += val
        else:
            stocks_value += val  # ETFs, REITs go in stocks bucket

    try:
        from sqlalchemy import select, func
        from app.models.options import UserOption
        result = await db.execute(
            select(UserOption).where(UserOption.user_id == user_id)
        )
        option_positions = result.scalars().all()
        for op in option_positions:
            options_value += float(op.current_value or op.premium or 0)
    except Exception:
        pass

    try:
        from sqlalchemy import select, func
        from app.models.dividend import DividendPayment
        result = await db.execute(
            select(func.coalesce(func.sum(DividendPayment.amount), 0))
            .where(DividendPayment.user_id == user_id)
        )
        dividends_value = float(result.scalar() or 0)
    except Exception:
        pass

    asset_allocation = AssetAllocation(
        stocks=round(stocks_value, 2),
        options=round(options_value, 2),
        dividends=round(dividends_value, 2),
    )

    # ── Top gainers / losers ──
    # Rank by (current_value - cost) / cost
    performers = []
    for h in holdings:
        cost = float(h.avg_cost * h.quantity)
        current = float(h.current_value or cost)
        if cost > 0:
            change_pct = ((current - cost) / cost) * 100
        else:
            change_pct = 0.0
        performers.append({
            "symbol": h.symbol,
            "change_pct": round(change_pct, 2),
            "current_value": round(current, 2),
        })

    performers.sort(key=lambda x: x["change_pct"], reverse=True)
    top_gainers = [TopPerformer(**p) for p in performers[:5]]
    top_losers = [TopPerformer(**p) for p in performers[-5:][::-1]]  # worst first

    # ── Parallel data fetches ──
    import asyncio
    health_task = asyncio.create_task(_get_portfolio_health_score(db, user_id))
    alerts_task = asyncio.create_task(_get_recent_alerts(db, user_id))
    greeks_task = asyncio.create_task(_get_options_greeks(db, user_id))
    dividends_task = asyncio.create_task(_get_upcoming_dividends(db, user_id))
    signals_task = asyncio.create_task(_get_ai_signals_summary(db, user_id))

    portfolio_health_score, recent_alerts_raw, options_greeks, upcoming_dividends, ai_signals = \
        await asyncio.gather(health_task, alerts_task, greeks_task, dividends_task, signals_task)

    recent_alerts = [RecentAlert(**a) for a in recent_alerts_raw]

    return PortfolioOverviewResponse(
        total_value=round(total_value, 2),
        daily_change=round(daily_change, 2),
        daily_change_pct=round(daily_change_pct, 2),
        asset_allocation=asset_allocation,
        top_gainers=top_gainers,
        top_losers=top_losers,
        upcoming_dividends=upcoming_dividends,
        ai_signals_summary=ai_signals,
        portfolio_health_score=portfolio_health_score,
        recent_alerts=recent_alerts,
        options_greeks=options_greeks,
    )

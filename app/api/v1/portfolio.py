"""
Portfolio management endpoints with multi-asset support.
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.models import User, UserHolding
from app.utils.auth import decode_access_token
from app.services.stock_service import StockService
from app.services.signal_engine_service import SignalEngineService, SignalType
from app.services.yfinance_service import YFinanceService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
logger = logging.getLogger(__name__)


class HoldingBase(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    asset_type: Literal["STOCK", "ETF", "BOND", "REIT", "OTHER"] = "STOCK"
    sector: Optional[str] = None
    dividend_yield: Optional[float] = None
    currency: Literal["USD", "TWD"] = "USD"
    dividend_frequency: Literal["QUARTERLY", "MONTHLY", "ANNUALLY", "NONE"] = "NONE"


class HoldingCreate(HoldingBase):
    pass


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = None
    avg_cost: Optional[float] = None
    asset_type: Optional[Literal["STOCK", "ETF", "BOND", "REIT", "OTHER"]] = None
    sector: Optional[str] = None
    dividend_yield: Optional[float] = None
    currency: Optional[Literal["USD", "TWD"]] = None
    dividend_frequency: Optional[Literal["QUARTERLY", "MONTHLY", "ANNUALLY", "NONE"]] = None


class HoldingResponse(HoldingBase):
    id: str
    symbol: str
    quantity: float
    avg_cost: float
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    gain_loss: Optional[float] = None
    gain_loss_pct: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    total_cost: float
    total_current_value: float
    total_gain_loss: float
    total_gain_loss_pct: float
    holdings_count: int


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
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def _get_current_price(symbol: str) -> Optional[float]:
    """Get current market price for a symbol."""
    try:
        stock_service = StockService()
        quote = await stock_service._fetch_quote(symbol)
        if quote:
            return quote.get("regularMarketPrice")
    except Exception as e:
        logger.warning(f"Failed to get quote for {symbol}: {e}")
    return None


@router.get("", response_model=dict)
async def get_portfolio(
    asset_type: Optional[str] = Query(None, description="Filter by asset type (STOCK, ETF, BOND, REIT, OTHER)"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's portfolio with current market values.
    
    Supports filtering by asset_type and sector.
    """
    query = select(UserHolding).where(UserHolding.user_id == user.id)
    if asset_type:
        query = query.where(UserHolding.asset_type == asset_type.upper())
    if sector:
        query = query.where(UserHolding.sector == sector)
    
    result = await db.execute(query)
    holdings = result.scalars().all()
    
    portfolio_items = []
    total_cost = 0.0
    total_current_value = 0.0
    
    for h in holdings:
        current_price = await _get_current_price(h.symbol)
        current_value = current_price * h.quantity if current_price else None
        cost_basis = h.avg_cost * h.quantity
        gain_loss = current_value - cost_basis if current_value else None
        gain_loss_pct = (gain_loss / cost_basis * 100) if gain_loss and cost_basis else None
        
        total_cost += cost_basis
        if current_value:
            total_current_value += current_value
        
        portfolio_items.append({
            "id": str(h.id),
            "symbol": h.symbol,
            "quantity": h.quantity,
            "avg_cost": h.avg_cost,
            "asset_type": h.asset_type,
            "sector": h.sector,
            "dividend_yield": h.dividend_yield,
            "currency": h.currency,
            "dividend_frequency": h.dividend_frequency,
            "current_price": current_price,
            "current_value": current_value,
            "gain_loss": gain_loss,
            "gain_loss_pct": gain_loss_pct,
            "created_at": h.created_at,
            "updated_at": h.updated_at,
        })
    
    total_gain_loss = total_current_value - total_cost if total_current_value else None
    total_gain_loss_pct = (total_gain_loss / total_cost * 100) if total_gain_loss and total_cost else None
    
    return {
        "holdings": portfolio_items,
        "summary": {
            "total_cost": total_cost,
            "total_current_value": total_current_value if total_current_value else 0.0,
            "total_gain_loss": total_gain_loss,
            "total_gain_loss_pct": total_gain_loss_pct,
            "holdings_count": len(holdings),
        }
    }


@router.get("/summary/by-asset-type", response_model=dict)
async def get_portfolio_by_asset_type(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get portfolio summary grouped by asset type.
    """
    result = await db.execute(
        select(
            UserHolding.asset_type,
            func.count(UserHolding.id).label("count"),
            func.sum(UserHolding.avg_cost * UserHolding.quantity).label("total_cost"),
        )
        .where(UserHolding.user_id == user.id)
        .group_by(UserHolding.asset_type)
    )
    rows = result.all()
    
    breakdown = []
    total_portfolio_value = 0.0
    
    for row in rows:
        holdings_result = await db.execute(
            select(UserHolding).where(
                UserHolding.user_id == user.id,
                UserHolding.asset_type == row.asset_type
            )
        )
        holdings = holdings_result.scalars().all()
        total_value = 0.0
        for h in holdings:
            current_price = await _get_current_price(h.symbol)
            if current_price:
                total_value += current_price * h.quantity
        
        total_portfolio_value += total_value
        breakdown.append({
            "asset_type": row.asset_type,
            "holdings_count": row.count,
            "total_cost": float(row.total_cost or 0),
            "total_current_value": total_value,
            "allocation_pct": None
        })
    
    for item in breakdown:
        if total_portfolio_value:
            item["allocation_pct"] = round((item["total_current_value"] / total_portfolio_value) * 100, 2)
    
    return {
        "asset_allocation": breakdown,
        "total_portfolio_value": total_portfolio_value
    }


@router.get("/summary/by-sector", response_model=dict)
async def get_portfolio_by_sector(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get portfolio summary grouped by sector.
    """
    result = await db.execute(
        select(
            UserHolding.sector,
            func.count(UserHolding.id).label("count"),
            func.sum(UserHolding.avg_cost * UserHolding.quantity).label("total_cost"),
        )
        .where(UserHolding.user_id == user.id, UserHolding.sector.isnot(None))
        .group_by(UserHolding.sector)
    )
    rows = result.all()
    
    breakdown = []
    total_portfolio_value = 0.0
    
    for row in rows:
        holdings_result = await db.execute(
            select(UserHolding).where(
                UserHolding.user_id == user.id,
                UserHolding.sector == row.sector
            )
        )
        holdings = holdings_result.scalars().all()
        total_value = 0.0
        for h in holdings:
            current_price = await _get_current_price(h.symbol)
            if current_price:
                total_value += current_price * h.quantity
        
        total_portfolio_value += total_value
        breakdown.append({
            "sector": row.sector,
            "holdings_count": row.count,
            "total_cost": float(row.total_cost or 0),
            "total_current_value": total_value,
            "allocation_pct": None
        })
    
    for item in breakdown:
        if total_portfolio_value:
            item["allocation_pct"] = round((item["total_current_value"] / total_portfolio_value) * 100, 2)
    
    return {
        "sector_allocation": breakdown,
        "total_portfolio_value": total_portfolio_value
    }


@router.post("/holdings", response_model=HoldingResponse)
async def create_holding(
    holding: HoldingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new holding to user's portfolio."""
    result = await db.execute(
        select(UserHolding).where(
            UserHolding.user_id == user.id,
            UserHolding.symbol == holding.symbol.upper()
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail=f"Holding for {holding.symbol} already exists")
    
    db_holding = UserHolding(
        user_id=user.id,
        symbol=holding.symbol.upper(),
        quantity=holding.quantity,
        avg_cost=holding.avg_cost,
        asset_type=holding.asset_type,
        sector=holding.sector,
        dividend_yield=holding.dividend_yield,
        currency=holding.currency,
        dividend_frequency=holding.dividend_frequency,
    )
    db.add(db_holding)
    await db.commit()
    await db.refresh(db_holding)
    
    current_price = await _get_current_price(db_holding.symbol)
    current_value = current_price * db_holding.quantity if current_price else None
    cost_basis = db_holding.avg_cost * db_holding.quantity
    gain_loss = current_value - cost_basis if current_value else None
    gain_loss_pct = (gain_loss / cost_basis * 100) if gain_loss and cost_basis else None
    
    return {
        "id": str(db_holding.id),
        "symbol": db_holding.symbol,
        "quantity": db_holding.quantity,
        "avg_cost": db_holding.avg_cost,
        "asset_type": db_holding.asset_type,
        "sector": db_holding.sector,
        "dividend_yield": db_holding.dividend_yield,
        "currency": db_holding.currency,
        "dividend_frequency": db_holding.dividend_frequency,
        "current_price": current_price,
        "current_value": current_value,
        "gain_loss": gain_loss,
        "gain_loss_pct": gain_loss_pct,
        "created_at": db_holding.created_at,
        "updated_at": db_holding.updated_at,
    }


@router.put("/holdings/{holding_id}", response_model=HoldingResponse)
async def update_holding(
    holding_id: str,
    update: HoldingUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing holding."""
    result = await db.execute(
        select(UserHolding).where(
            UserHolding.id == holding_id,
            UserHolding.user_id == user.id
        )
    )
    db_holding = result.scalar_one_or_none()
    if not db_holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    
    if update.quantity is not None:
        db_holding.quantity = update.quantity
    if update.avg_cost is not None:
        db_holding.avg_cost = update.avg_cost
    if update.asset_type is not None:
        db_holding.asset_type = update.asset_type
    if update.sector is not None:
        db_holding.sector = update.sector
    if update.dividend_yield is not None:
        db_holding.dividend_yield = update.dividend_yield
    if update.currency is not None:
        db_holding.currency = update.currency
    if update.dividend_frequency is not None:
        db_holding.dividend_frequency = update.dividend_frequency
    
    await db.commit()
    await db.refresh(db_holding)
    
    current_price = await _get_current_price(db_holding.symbol)
    current_value = current_price * db_holding.quantity if current_price else None
    cost_basis = db_holding.avg_cost * db_holding.quantity
    gain_loss = current_value - cost_basis if current_value else None
    gain_loss_pct = (gain_loss / cost_basis * 100) if gain_loss and cost_basis else None
    
    return {
        "id": str(db_holding.id),
        "symbol": db_holding.symbol,
        "quantity": db_holding.quantity,
        "avg_cost": db_holding.avg_cost,
        "asset_type": db_holding.asset_type,
        "sector": db_holding.sector,
        "dividend_yield": db_holding.dividend_yield,
        "currency": db_holding.currency,
        "dividend_frequency": db_holding.dividend_frequency,
        "current_price": current_price,
        "current_value": current_value,
        "gain_loss": gain_loss,
        "gain_loss_pct": gain_loss_pct,
        "created_at": db_holding.created_at,
        "updated_at": db_holding.updated_at,
    }


@router.delete("/holdings/{holding_id}")
async def delete_holding(
    holding_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a holding from portfolio."""
    result = await db.execute(
        select(UserHolding).where(
            UserHolding.id == holding_id,
            UserHolding.user_id == user.id
        )
    )
    db_holding = result.scalar_one_or_none()
    if not db_holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    
    await db.delete(db_holding)
    await db.commit()
    
    return {"message": "Holding deleted successfully"}


@router.get("/signals", response_model=dict)
async def get_portfolio_signals(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI signals for all stock holdings in user's portfolio.
    
    Returns holdings with their corresponding buy/sell/hold signals,
    confidence levels, and bullish/bearish factors.
    Only includes holdings with asset_type=STOCK.
    """
    # Get only STOCK holdings (ETF/BOND signals not meaningful)
    result = await db.execute(
        select(UserHolding).where(
            UserHolding.user_id == user.id,
            UserHolding.asset_type == "STOCK"
        )
    )
    holdings = result.scalars().all()
    
    signal_service = SignalEngineService()
    holdings_with_signals = []
    conflicts = []
    
    for h in holdings:
        # Get current price
        current_price = await _get_current_price(h.symbol)
        current_value = current_price * h.quantity if current_price else None
        cost_basis = h.avg_cost * h.quantity
        gain_loss = current_value - cost_basis if current_value else None
        gain_loss_pct = (gain_loss / cost_basis * 100) if gain_loss and cost_basis else None
        
        # Get signal from AI engine
        signal_result = await signal_service.get_signal(h.symbol)
        
        holding_data = {
            "id": str(h.id),
            "symbol": h.symbol,
            "quantity": h.quantity,
            "avg_cost": h.avg_cost,
            "current_price": current_price,
            "current_value": current_value,
            "gain_loss": gain_loss,
            "gain_loss_pct": gain_loss_pct,
        }
        
        if signal_result:
            # Determine if there's a conflict (holding but signal is bearish)
            is_conflict = signal_result.overall_signal in (SignalType.SELL, SignalType.STRONG_SELL)
            
            signal_data = {
                "signal": signal_result.overall_signal.value,
                "signal_label": _get_signal_label(signal_result.overall_signal),
                "confidence": signal_result.confidence,
                "summary": signal_result.summary,
                "bullish_factors": signal_result.bullish_factors,
                "bearish_factors": signal_result.bearish_factors,
                "indicators": [
                    {
                        "indicator": ind.indicator,
                        "value": ind.value,
                        "signal": ind.signal.value,
                        "reasoning": ind.reasoning,
                    }
                    for ind in signal_result.indicators
                ],
            }
            
            if is_conflict:
                conflicts.append({
                    "holding": holding_data,
                    "signal": signal_data,
                })
            
            holdings_with_signals.append({
                "holding": holding_data,
                "signal": signal_data,
                "is_conflict": is_conflict,
            })
    
    # Sort by confidence (highest first)
    holdings_with_signals.sort(key=lambda x: x["signal"]["confidence"], reverse=True)
    
    return {
        "holdings": holdings_with_signals,
        "conflicts": conflicts,
        "total_holdings": len(holdings_with_signals),
        "total_conflicts": len(conflicts),
    }


def _get_signal_label(signal: SignalType) -> str:
    """Get human-readable label for signal."""
    labels = {
        SignalType.STRONG_BUY: "強烈買入",
        SignalType.BUY: "買入",
        SignalType.HOLD: "持有",
        SignalType.SELL: "賣出",
        SignalType.STRONG_SELL: "強烈賣出",
    }
    return labels.get(signal, "未知")


@router.get("/report/pdf")
async def get_portfolio_pdf(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate and download a PDF report of the user's portfolio.
    
    Includes portfolio summary, holdings table with gain/loss, and AI signals.
    """
    from fastapi.responses import Response
    from app.services.report_service import generate_portfolio_pdf
    
    # Get holdings
    result = await db.execute(
        select(UserHolding).where(UserHolding.user_id == user.id)
    )
    holdings = result.scalars().all()
    
    portfolio_items = []
    total_cost = 0.0
    total_current_value = 0.0
    
    for h in holdings:
        current_price = await _get_current_price(h.symbol)
        current_value = current_price * h.quantity if current_price else None
        cost_basis = h.avg_cost * h.quantity
        gain_loss = current_value - cost_basis if current_value else None
        gain_loss_pct = (gain_loss / cost_basis * 100) if gain_loss and cost_basis else None
        
        total_cost += cost_basis
        if current_value:
            total_current_value += current_value
        
        portfolio_items.append({
            "id": str(h.id),
            "symbol": h.symbol,
            "quantity": h.quantity,
            "avg_cost": h.avg_cost,
            "asset_type": h.asset_type,
            "current_price": current_price,
            "current_value": current_value,
            "gain_loss": gain_loss,
            "gain_loss_pct": gain_loss_pct,
        })
    
    total_gain_loss = total_current_value - total_cost if total_current_value else None
    total_gain_loss_pct = (total_gain_loss / total_cost * 100) if total_gain_loss and total_cost else None
    
    summary = {
        "total_cost": total_cost,
        "total_current_value": total_current_value,
        "total_gain_loss": total_gain_loss,
        "total_gain_loss_pct": total_gain_loss_pct,
    }
    
    # Try to get signals data (optional, don't fail if it errors)
    signals_data = None
    try:
        signal_service = SignalEngineService()
        holdings_with_signals = []
        for h in holdings:
            if h.asset_type != "STOCK":
                continue
            signal_result = await signal_service.get_signal(h.symbol)
            if signal_result:
                holding_data = {
                    "symbol": h.symbol,
                    "quantity": h.quantity,
                    "avg_cost": h.avg_cost,
                    "current_price": await _get_current_price(h.symbol),
                    "current_value": (await _get_current_price(h.symbol) or 0) * h.quantity if await _get_current_price(h.symbol) else None,
                }
                signal_data = {
                    "signal": signal_result.overall_signal.value,
                    "signal_label": _get_signal_label(signal_result.overall_signal),
                    "confidence": signal_result.confidence,
                    "summary": signal_result.summary,
                }
                holdings_with_signals.append({
                    "holding": holding_data,
                    "signal": signal_data,
                })
        if holdings_with_signals:
            signals_data = {"holdings": holdings_with_signals}
    except Exception:
        pass  # Signals are optional for PDF
    
    pdf_bytes = generate_portfolio_pdf(portfolio_items, summary, signals_data)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=portfolio-report.pdf"
        }
    )


# Risk Analytics endpoint
@router.get("/risk-analytics", response_model=dict)
async def get_portfolio_risk_analytics(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
    lookback_days: int = 90,
):
    """
    Get portfolio risk analytics.

    Calculates VaR, Sharpe Ratio, Max Drawdown, and vs S&P 500 comparison.

    Args:
        lookback_days: Number of days of historical data to use (default 90).

    Returns:
        Risk metrics including VaR, Sharpe Ratio, Max Drawdown.
    """
    from app.services.risk_analytics_service import RiskAnalyticsService
    from app.services.yfinance_service import YFinanceService

    # Extract user ID from token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")

    # Get user holdings
    result = await db.execute(
        select(UserHolding).where(UserHolding.user_id == user_id)
    )
    holdings = result.scalars().all()

    if not holdings:
        return {
            "portfolio_value": 0,
            "var_95": 0,
            "var_99": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "max_drawdown_percent": 0,
            "vs_sp500_return": 0,
            "sp500_return": 0,
            "portfolio_return": 0,
            "volatility": 0,
            "timestamp": datetime.now().isoformat(),
        }

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
            except Exception:
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
            except Exception:
                pass
    finally:
        await yfinance.close()

    # Get S&P 500 historical data
    sp500_historical = []
    try:
        sp500_history = await yfinance.get_historical(
            symbol="^GSPC",
            period=f"{lookback_days}d",
        )
        if sp500_history and sp500_history.closes:
            sp500_historical = sp500_history.closes
    except Exception:
        pass

    # Calculate risk metrics
    risk_service = RiskAnalyticsService()
    metrics = await risk_service.calculate_risk_metrics(
        holdings=holdings_data,
        prices=prices,
        historical_prices=historical_prices,
        sp500_historical=sp500_historical,
    )

    return {
        "portfolio_value": metrics.portfolio_value,
        "var_95": metrics.var_95,
        "var_99": metrics.var_99,
        "sharpe_ratio": metrics.sharpe_ratio,
        "max_drawdown": metrics.max_drawdown,
        "max_drawdown_percent": metrics.max_drawdown_percent,
        "vs_sp500_return": metrics.vs_sp500_return,
        "sp500_return": metrics.sp500_return,
        "portfolio_return": metrics.portfolio_return,
        "volatility": metrics.volatility,
        "timestamp": metrics.timestamp,
    }


@router.get("/drift-detection", response_model=dict)
async def get_portfolio_drift_detection(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
):
    """
    Get portfolio drift detection analysis.

    Compares current holdings against AI Signal recommendations
    and provides rebalancing suggestions.

    Returns:
        Drift analysis with holding details and rebalancing trades.
    """
    from app.services.drift_detection_service import DriftDetectionService
    from app.services.signal_engine_service import SignalEngineService

    # Extract user ID from token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload["sub"]

    # Get user holdings
    result = await db.execute(
        select(UserHolding).where(UserHolding.user_id == user_id)
    )
    holdings = result.scalars().all()

    if not holdings:
        return {
            "total_value": 0,
            "drift_score": 0,
            "holdings": [],
            "rebalancing_trades": [],
            "rebalancing_total_buy": 0,
            "rebalancing_total_sell": 0,
            "timestamp": "",
        }

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
            except Exception:
                prices[symbol] = 0
    finally:
        await yfinance.close()

    # Calculate portfolio value
    portfolio_value = sum(
        h["quantity"] * prices.get(h["symbol"], 0)
        for h in holdings_data
    )

    # Get signals for each holding
    signal_engine = SignalEngineService()
    signals = {}

    try:
        for symbol in symbols:
            try:
                signal = await signal_engine.get_signal(symbol)
                if signal:
                    signals[symbol] = {
                        "signal": signal.overall_signal.value,
                        "confidence": signal.confidence,
                    }
                else:
                    signals[symbol] = {"signal": "HOLD", "confidence": 0.5}
            except Exception:
                signals[symbol] = {"signal": "HOLD", "confidence": 0.5}
    finally:
        await signal_engine.close()

    # Calculate drift
    drift_service = DriftDetectionService()
    drift_result = await drift_service.calculate_drift(
        holdings=holdings_data,
        prices=prices,
        signals=signals,
        portfolio_value=portfolio_value,
    )

    return {
        "total_value": drift_result.total_value,
        "drift_score": drift_result.drift_score,
        "holdings": [
            {
                "symbol": h.symbol,
                "current_quantity": h.current_quantity,
                "current_value": h.current_value,
                "current_weight": h.current_weight,
                "recommended_signal": h.recommended_signal,
                "recommended_weight": h.recommended_weight,
                "drift_percentage": h.drift_percentage,
                "action": h.action,
                "action_quantity": h.action_quantity,
                "action_value": h.action_value,
            }
            for h in drift_result.holdings
        ],
        "rebalancing_trades": [
            {
                "symbol": h.symbol,
                "action": h.action,
                "quantity": h.action_quantity,
                "value": h.action_value,
            }
            for h in drift_result.rebalancing_trades
        ],
        "rebalancing_total_buy": drift_result.rebalancing_total_buy,
        "rebalancing_total_sell": drift_result.rebalancing_total_sell,
        "timestamp": drift_result.timestamp,
    }


@router.get("/tax-loss-harvesting", response_model=dict)
async def get_tax_loss_harvesting(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
    risk_tolerance: str = "MEDIUM",
):
    """
    Get tax-loss harvesting opportunities.

    Identifies positions with unrealized losses that could be harvested
    for tax benefits, while avoiding wash sale rule violations.

    Args:
        risk_tolerance: User's risk tolerance (LOW, MEDIUM, HIGH)

    Returns:
        Tax-loss harvesting analysis with candidates and suggestions.
    """
    from app.services.tax_loss_harvesting_service import TaxLossHarvestingService

    # Extract user ID from token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload["sub"]

    # Get user holdings
    result = await db.execute(
        select(UserHolding).where(UserHolding.user_id == user_id)
    )
    holdings = result.scalars().all()

    if not holdings:
        return {
            "total_unrealized_loss": 0,
            "total_estimated_tax_savings": 0,
            "candidates": [],
            "harvesting_trades": [],
            "total_harvest_value": 0,
            "replacement_suggestions": [],
            "capital_gains_rate": 0.20,
            "timestamp": "",
        }

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
            except Exception:
                prices[symbol] = 0
    finally:
        await yfinance.close()

    # Calculate tax-loss harvesting opportunities
    tax_service = TaxLossHarvestingService()
    result_data = tax_service.calculate_harvesting_opportunities(
        holdings=holdings_data,
        prices=prices,
        risk_tolerance=risk_tolerance,
    )

    return {
        "total_unrealized_loss": result_data.total_unrealized_loss,
        "total_estimated_tax_savings": result_data.total_estimated_tax_savings,
        "candidates": [
            {
                "symbol": c.symbol,
                "quantity": c.quantity,
                "current_price": c.current_price,
                "avg_cost": c.avg_cost,
                "unrealized_loss": c.unrealized_loss,
                "unrealized_loss_percent": c.unrealized_loss_percent,
                "estimated_tax_savings": c.estimated_tax_savings,
                "wash_sale_risk": c.wash_sale_risk,
                "replacement_candidate": c.replacement_candidate,
                "action": c.action,
            }
            for c in result_data.candidates
        ],
        "harvesting_trades": [
            {
                "symbol": c.symbol,
                "quantity": c.quantity,
                "unrealized_loss": c.unrealized_loss,
                "estimated_tax_savings": c.estimated_tax_savings,
                "replacement_candidate": c.replacement_candidate,
            }
            for c in result_data.harvesting_trades
        ],
        "total_harvest_value": result_data.total_harvest_value,
        "replacement_suggestions": result_data.replacement_suggestions,
        "capital_gains_rate": result_data.capital_gains_rate,
        "timestamp": result_data.timestamp,
    }


@router.post("/backtest", response_model=dict)
async def run_portfolio_backtest(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
    symbol: str = "AAPL",
    period: str = "1y",
    strategy: str = "sma_crossover",
    initial_capital: float = 10000.0,
):
    """
    Run backtest for a trading strategy.

    Args:
        symbol: Stock symbol to backtest
        period: Time period (e.g., '1y', '6m', '2y')
        strategy: Strategy name (default 'sma_crossover')
        initial_capital: Starting capital (default $10,000)

    Returns:
        Backtest results with performance metrics and trade history.
    """
    from app.services.backtesting_service import PortfolioBacktestingService

    # Get historical data
    yfinance = YFinanceService()
    try:
        history = await yfinance.get_historical(symbol, period=period)
        if not history or not history.closes:
            return {"error": f"No historical data for {symbol}"}

        prices = history.closes
        dates = history.dates if hasattr(history, 'dates') else [f"Day_{i}" for i in range(len(prices))]

    except Exception as e:
        return {"error": f"Failed to get historical data: {str(e)}"}
    finally:
        await yfinance.close()

    # Run backtest
    backtest_service = PortfolioBacktestingService()
    try:
        result = await backtest_service.run_backtest(
            symbol=symbol,
            historical_prices=prices,
            dates=dates,
            strategy=strategy,
            initial_capital=initial_capital,
        )

        return {
            "symbol": result.symbol,
            "strategy": result.strategy,
            "start_date": result.start_date,
            "end_date": result.end_date,
            "initial_capital": result.initial_capital,
            "final_value": result.final_value,
            "metrics": {
                "total_return": result.metrics.total_return,
                "total_return_percent": result.metrics.total_return_percent,
                "sharpe_ratio": result.metrics.sharpe_ratio,
                "max_drawdown": result.metrics.max_drawdown,
                "max_drawdown_percent": result.metrics.max_drawdown_percent,
                "volatility": result.metrics.volatility,
                "win_rate": result.metrics.win_rate,
                "trade_count": result.metrics.trade_count,
                "benchmark_return": result.metrics.benchmark_return,
                "alpha": result.metrics.alpha,
            },
            "trades": [
                {
                    "date": t.date,
                    "action": t.action,
                    "symbol": t.symbol,
                    "quantity": t.quantity,
                    "price": t.price,
                    "value": t.value,
                }
                for t in result.trades
            ],
            "equity_curve": result.equity_curve,
            "timestamp": result.metrics.timestamp,
        }

    except Exception as e:
        return {"error": f"Backtest failed: {str(e)}"}


@router.get("/currencies")
async def get_supported_currencies():
    """
    Get list of supported currencies.

    Returns:
        List of supported currency codes and info.
    """
    from app.services.multi_currency_service import MultiCurrencyService

    service = MultiCurrencyService()
    currencies = await service.get_supported_currencies()

    return {
        "currencies": currencies,
        "count": len(currencies),
    }


@router.get("/convert")
async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
):
    """
    Convert amount between currencies.

    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code

    Returns:
        Converted amount and exchange rate.
    """
    from app.services.multi_currency_service import MultiCurrencyService

    service = MultiCurrencyService()
    rate = await service.get_exchange_rate(from_currency, to_currency)
    converted = await service.convert_amount(amount, from_currency, to_currency)

    return {
        "from_currency": from_currency,
        "to_currency": to_currency,
        "original_amount": amount,
        "converted_amount": round(converted, 2),
        "exchange_rate": round(rate, 4),
        "formatted": service.format_currency(converted, to_currency),
    }


@router.get("/portfolio/{currency}")
async def get_portfolio_in_currency(
    currency: str,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
):
    """
    Get portfolio summary in specific currency.

    Args:
        currency: Target currency code (USD, TWD, JPY, etc.)

    Returns:
        Portfolio summary in target currency.
    """
    from app.services.multi_currency_service import MultiCurrencyService

    # Extract user ID from token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload["sub"]

    # Get user holdings
    result = await db.execute(
        select(UserHolding).where(UserHolding.user_id == user_id)
    )
    holdings = result.scalars().all()

    if not holdings:
        return {
            "base_currency": "USD",
            "display_currency": currency,
            "holdings": [],
            "total_value": 0,
            "total_cost": 0,
            "total_gain_loss": 0,
        }

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
            except Exception:
                prices[symbol] = 0
    finally:
        await yfinance.close()

    # Convert to target currency
    service = MultiCurrencyService()
    portfolio = await service.get_portfolio_in_currency(
        holdings=holdings_data,
        prices=prices,
        target_currency=currency,
    )

    return portfolio

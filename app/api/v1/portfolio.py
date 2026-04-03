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

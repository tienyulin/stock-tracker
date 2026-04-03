"""
Portfolio management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
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


class HoldingCreate(HoldingBase):
    pass


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = None
    avg_cost: Optional[float] = None


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


@router.get("", response_model=dict)
async def get_portfolio(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's portfolio with current market values.
    
    Returns list of holdings with current prices and gain/loss calculations.
    """
    # Get all holdings for user
    result = await db.execute(
        select(UserHolding).where(UserHolding.user_id == user.id)
    )
    holdings = result.scalars().all()
    
    stock_service = StockService()
    portfolio_items = []
    total_cost = 0.0
    total_current_value = 0.0
    
    for h in holdings:
        # Get current price
        current_price = None
        try:
            quote = await stock_service.get_quote(h.symbol)
            if quote:
                current_price = quote.get("regularMarketPrice")
        except Exception as e:
            logger.warning(f"Failed to get quote for {h.symbol}: {e}")
        
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
            "total_current_value": total_current_value,
            "total_gain_loss": total_gain_loss,
            "total_gain_loss_pct": total_gain_loss_pct,
            "holdings_count": len(holdings),
        }
    }


@router.post("/holdings", response_model=HoldingResponse)
async def create_holding(
    holding: HoldingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new holding to user's portfolio."""
    # Check if holding already exists for this symbol
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
    )
    db.add(db_holding)
    await db.commit()
    await db.refresh(db_holding)
    
    return {
        "id": str(db_holding.id),
        "symbol": db_holding.symbol,
        "quantity": db_holding.quantity,
        "avg_cost": db_holding.avg_cost,
        "current_price": None,
        "current_value": None,
        "gain_loss": None,
        "gain_loss_pct": None,
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
    
    await db.commit()
    await db.refresh(db_holding)
    
    # Get current price
    stock_service = StockService()
    current_price = None
    try:
        quote = await stock_service.get_quote(db_holding.symbol)
        if quote:
            current_price = quote.get("regularMarketPrice")
    except Exception as e:
        logger.warning(f"Failed to get quote for {db_holding.symbol}: {e}")
    
    current_value = current_price * db_holding.quantity if current_price else None
    cost_basis = db_holding.avg_cost * db_holding.quantity
    gain_loss = current_value - cost_basis if current_value else None
    gain_loss_pct = (gain_loss / cost_basis * 100) if gain_loss and cost_basis else None
    
    return {
        "id": str(db_holding.id),
        "symbol": db_holding.symbol,
        "quantity": db_holding.quantity,
        "avg_cost": db_holding.avg_cost,
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

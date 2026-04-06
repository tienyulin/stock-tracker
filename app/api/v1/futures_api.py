"""
Futures & Derivatives API
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.futures import FuturesPosition, FuturesContract, FuturesPriceAlert
from app.models.user import User


router = APIRouter(prefix="/futures", tags=["futures"])


# Pydantic Schemas
class FuturesPositionCreate(BaseModel):
    symbol: str
    contract_size: float = 1.0
    entry_price: float
    current_price: Optional[float] = None
    quantity: int = 1
    position_type: str  # LONG or SHORT
    entry_date: Optional[str] = None
    expiry_date: str
    margin_required: Optional[float] = None
    maintenance_margin: Optional[float] = None
    broker: Optional[str] = None
    notes: Optional[str] = None


class FuturesPositionUpdate(BaseModel):
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    notes: Optional[str] = None


class FuturesPositionResponse(BaseModel):
    id: str
    symbol: str
    contract_size: float
    entry_price: float
    current_price: Optional[float]
    quantity: int
    position_type: str
    entry_date: str
    expiry_date: str
    margin_required: Optional[float]
    unrealized_pnl: Optional[float]
    realized_pnl: float
    is_active: bool
    broker: Optional[str]

    class Config:
        from_attributes = True


class FuturesSummaryResponse(BaseModel):
    total_positions: int
    total_unrealized_pnl: float
    total_realized_pnl: float
    long_count: int
    short_count: int
    expiring_soon: int  # Expiring within 7 days


class LeverageMetricsResponse(BaseModel):
    total_exposure: float
    total_margin_used: float
    leverage_ratio: float
    maintenance_margin_required: float


# CRUD Operations
@router.post("/positions", response_model=FuturesPositionResponse)
def create_futures_position(
    position: FuturesPositionCreate,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Create a new futures position."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        entry_dt = datetime.fromisoformat(position.entry_date.replace("Z", "+00:00")) if position.entry_date else datetime.now()
        expiry_dt = datetime.fromisoformat(position.expiry_date.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    db_position = FuturesPosition(
        user_id=user_id,
        symbol=position.symbol.upper(),
        contract_size=position.contract_size,
        entry_price=position.entry_price,
        current_price=position.current_price,
        quantity=position.quantity,
        position_type=position.position_type.upper(),
        entry_date=entry_dt,
        expiry_date=expiry_dt,
        margin_required=position.margin_required,
        maintenance_margin=position.maintenance_margin,
        broker=position.broker,
        notes=position.notes
    )

    db.add(db_position)
    db.commit()
    db.refresh(db_position)

    return FuturesPositionResponse(
        id=str(db_position.id),
        symbol=db_position.symbol,
        contract_size=float(db_position.contract_size),
        entry_price=float(db_position.entry_price),
        current_price=float(db_position.current_price) if db_position.current_price else None,
        quantity=db_position.quantity,
        position_type=db_position.position_type,
        entry_date=db_position.entry_date.isoformat(),
        expiry_date=db_position.expiry_date.isoformat(),
        margin_required=float(db_position.margin_required) if db_position.margin_required else None,
        unrealized_pnl=float(db_position.unrealized_pnl) if db_position.unrealized_pnl else 0.0,
        realized_pnl=float(db_position.realized_pnl),
        is_active=db_position.is_active,
        broker=db_position.broker
    )


@router.get("/positions", response_model=list[FuturesPositionResponse])
def list_futures_positions(
    user_id: UUID = Query(...),
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all futures positions for a user."""
    query = db.query(FuturesPosition).filter(FuturesPosition.user_id == user_id)
    if active_only:
        query = query.filter(FuturesPosition.is_active == True)
    positions = query.order_by(FuturesPosition.expiry_date).all()

    return [
        FuturesPositionResponse(
            id=str(p.id),
            symbol=p.symbol,
            contract_size=float(p.contract_size),
            entry_price=float(p.entry_price),
            current_price=float(p.current_price) if p.current_price else None,
            quantity=p.quantity,
            position_type=p.position_type,
            entry_date=p.entry_date.isoformat(),
            expiry_date=p.expiry_date.isoformat(),
            margin_required=float(p.margin_required) if p.margin_required else None,
            unrealized_pnl=float(p.unrealized_pnl) if p.unrealized_pnl else 0.0,
            realized_pnl=float(p.realized_pnl),
            is_active=p.is_active,
            broker=p.broker
        )
        for p in positions
    ]


@router.get("/positions/{position_id}", response_model=FuturesPositionResponse)
def get_futures_position(
    position_id: UUID,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get a specific futures position."""
    position = db.query(FuturesPosition).filter(
        FuturesPosition.id == position_id,
        FuturesPosition.user_id == user_id
    ).first()

    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    return FuturesPositionResponse(
        id=str(position.id),
        symbol=position.symbol,
        contract_size=float(position.contract_size),
        entry_price=float(position.entry_price),
        current_price=float(position.current_price) if position.current_price else None,
        quantity=position.quantity,
        position_type=position.position_type,
        entry_date=position.entry_date.isoformat(),
        expiry_date=position.expiry_date.isoformat(),
        margin_required=float(position.margin_required) if position.margin_required else None,
        unrealized_pnl=float(position.unrealized_pnl) if position.unrealized_pnl else 0.0,
        realized_pnl=float(position.realized_pnl),
        is_active=position.is_active,
        broker=position.broker
    )


@router.patch("/positions/{position_id}")
def update_futures_position(
    position_id: UUID,
    update: FuturesPositionUpdate,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Update a futures position (current price, close position, etc.)."""
    position = db.query(FuturesPosition).filter(
        FuturesPosition.id == position_id,
        FuturesPosition.user_id == user_id
    ).first()

    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    if update.current_price is not None:
        position.current_price = update.current_price
        # Recalculate unrealized P&L
        price_diff = float(position.current_price) - float(position.entry_price)
        if position.position_type == "LONG":
            position.unrealized_pnl = price_diff * float(position.contract_size) * position.quantity
        else:
            position.unrealized_pnl = -price_diff * float(position.contract_size) * position.quantity

    if update.unrealized_pnl is not None:
        position.unrealized_pnl = update.unrealized_pnl

    if update.notes is not None:
        position.notes = update.notes

    db.commit()
    return {"status": "updated", "position_id": str(position_id)}


@router.delete("/positions/{position_id}")
def close_futures_position(
    position_id: UUID,
    user_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Close a futures position (mark as inactive, realize P&L)."""
    position = db.query(FuturesPosition).filter(
        FuturesPosition.id == position_id,
        FuturesPosition.user_id == user_id
    ).first()

    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    position.is_active = False
    position.realized_pnl = (position.realized_pnl or 0) + (position.unrealized_pnl or 0)
    position.unrealized_pnl = 0

    db.commit()
    return {"status": "closed", "position_id": str(position_id)}


# Analytics
@router.get("/summary/{user_id}", response_model=FuturesSummaryResponse)
def get_futures_summary(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """Get futures portfolio summary."""
    positions = db.query(FuturesPosition).filter(
        FuturesPosition.user_id == user_id,
        FuturesPosition.is_active == True
    ).all()

    total_unrealized = sum(float(p.unrealized_pnl or 0) for p in positions)
    total_realized = sum(float(p.realized_pnl or 0) for p in positions)
    long_count = sum(1 for p in positions if p.position_type == "LONG")
    short_count = sum(1 for p in positions if p.position_type == "SHORT")

    # Expiring within 7 days
    now = datetime.now()
    expiring_soon = sum(
        1 for p in positions
        if (p.expiry_date - now).days <= 7
    )

    return FuturesSummaryResponse(
        total_positions=len(positions),
        total_unrealized_pnl=round(total_unrealized, 2),
        total_realized_pnl=round(total_realized, 2),
        long_count=long_count,
        short_count=short_count,
        expiring_soon=expiring_soon
    )


@router.get("/leverage/{user_id}", response_model=LeverageMetricsResponse)
def get_leverage_metrics(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """Calculate leverage and margin metrics."""
    positions = db.query(FuturesPosition).filter(
        FuturesPosition.user_id == user_id,
        FuturesPosition.is_active == True
    ).all()

    total_exposure = 0.0
    total_margin = 0.0
    maintenance_margin = 0.0

    for p in positions:
        if p.current_price:
            price = float(p.current_price)
        else:
            price = float(p.entry_price)

        exposure = price * float(p.contract_size) * p.quantity
        total_exposure += exposure

        if p.margin_required:
            total_margin += float(p.margin_required)
        if p.maintenance_margin:
            maintenance_margin += float(p.maintenance_margin)

    leverage = total_exposure / total_margin if total_margin > 0 else 0

    return LeverageMetricsResponse(
        total_exposure=round(total_exposure, 2),
        total_margin_used=round(total_margin, 2),
        leverage_ratio=round(leverage, 2),
        maintenance_margin_required=round(maintenance_margin, 2)
    )


# Alerts
@router.post("/alerts")
def create_futures_alert(
    user_id: UUID = Query(...),
    symbol: str = Query(...),
    alert_type: str = Query(...),
    threshold_price: Optional[float] = None,
    days_before_expiry: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Create a price or expiry alert for futures."""
    alert = FuturesPriceAlert(
        user_id=user_id,
        symbol=symbol.upper(),
        alert_type=alert_type,
        threshold_price=threshold_price,
        days_before_expiry=days_before_expiry
    )
    db.add(alert)
    db.commit()
    return {"status": "created", "alert_id": str(alert.id)}

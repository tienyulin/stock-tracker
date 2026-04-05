"""
Options Tracking API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

from app.core.database import get_db
from app.models.models import User
from app.models.options import OptionPosition
from app.services.options_service import OptionsService, GreekLetters
from app.utils.auth import decode_access_token

router = APIRouter(prefix="/options", tags=["options"])


async def get_current_user_id(authorization: str = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


async def get_current_user(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# --- Schemas ---

class GreekLettersSchema(BaseModel):
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    iv: float
    theoretical_price: float


class OptionQuoteSchema(BaseModel):
    strike: float
    expiry: str
    option_type: str
    last_price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    iv: float
    in_the_money: bool
    moneyness: float
    greeks: GreekLettersSchema


class OptionsChainSchema(BaseModel):
    symbol: str
    spot_price: float
    risk_free_rate: float
    expiry_date: str
    calls: list[OptionQuoteSchema]
    puts: list[OptionQuoteSchema]


class OptionPositionSchema(BaseModel):
    id: str
    underlying_symbol: str
    strike_price: float
    expiry_date: str
    option_type: str
    quantity: float
    premium: float
    open_date: str
    close_date: Optional[str]
    is_closed: bool
    notes: Optional[str]
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None


class OptionPositionCreate(BaseModel):
    underlying_symbol: str
    strike_price: float
    expiry_date: str  # YYYY-MM-DD
    option_type: Literal["CALL", "PUT"]
    quantity: float
    premium: float
    notes: Optional[str] = None


class GreeksRequestSchema(BaseModel):
    symbol: str
    strike: float
    expiry: str
    option_type: Literal["CALL", "PUT"]
    iv: Optional[float] = None


# --- Endpoints ---

@router.get("/{symbol}", response_model=OptionsChainSchema)
async def get_options_chain(
    symbol: str,
    expiry: Optional[str] = Query(None, description="Expiry date YYYY-MM-DD"),
    strike_count: int = Query(10, ge=1, le=50, description="Strikes around ATM"),
    user: User = Depends(get_current_user),
):
    """
    Get options chain for a symbol with Greek letters.
    """
    async with OptionsService() as svc:
        chain = await svc.get_options_chain(symbol.upper(), expiry=expiry, strike_count=strike_count)

    if not chain:
        raise HTTPException(status_code=404, detail=f"No options data found for {symbol}")

    def _quote_schema(q):
        return OptionQuoteSchema(
            strike=q.strike,
            expiry=q.expiry,
            option_type=q.option_type,
            last_price=q.last_price,
            bid=q.bid,
            ask=q.ask,
            volume=q.volume,
            open_interest=q.open_interest,
            iv=q.iv,
            in_the_money=q.in_the_money,
            moneyness=q.moneyness,
            greeks=GreekLettersSchema(
                delta=round(q.greeks.delta, 4),
                gamma=round(q.greeks.gamma, 4),
                theta=round(q.greeks.theta, 4),
                vega=round(q.greeks.vega, 4),
                rho=round(q.greeks.rho, 4),
                iv=round(q.greeks.iv, 4),
                theoretical_price=round(q.greeks.theoretical_price, 4),
            ),
        )

    return OptionsChainSchema(
        symbol=chain.symbol,
        spot_price=chain.spot_price,
        risk_free_rate=chain.risk_free_rate,
        expiry_date=chain.expiry_date,
        calls=[_quote_schema(q) for q in chain.calls],
        puts=[_quote_schema(q) for q in chain.puts],
    )


@router.get("/{symbol}/greeks", response_model=GreekLettersSchema)
async def get_greeks(
    symbol: str,
    strike: float = Query(..., description="Strike price"),
    expiry: str = Query(..., description="Expiry date YYYY-MM-DD"),
    option_type: Literal["CALL", "PUT"] = Query(...),
    iv: Optional[float] = Query(None, description="Implied volatility override"),
    user: User = Depends(get_current_user),
):
    """
    Get Greek letters for a specific option contract.
    """
    async with OptionsService() as svc:
        greeks = await svc.get_greeks(symbol.upper(), strike, expiry, option_type, iv=iv)

    if not greeks:
        raise HTTPException(status_code=404, detail="Could not calculate Greeks")

    return GreekLettersSchema(
        delta=round(greeks.delta, 4),
        gamma=round(greeks.gamma, 4),
        theta=round(greeks.theta, 4),
        vega=round(greeks.vega, 4),
        rho=round(greeks.rho, 4),
        iv=round(greeks.iv, 4),
        theoretical_price=round(greeks.theoretical_price, 4),
    )


# --- Portfolio Options Endpoints ---

@router.get("/portfolio/positions", response_model=list[OptionPositionSchema])
async def list_option_positions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    include_closed: bool = Query(False),
):
    """
    List all option positions in user's portfolio.
    """
    query = select(OptionPosition).where(OptionPosition.user_id == user.id)
    if not include_closed:
        query = query.where(OptionPosition.is_closed == False)  # noqa: E712

    result = await db.execute(query)
    positions = result.scalars().all()

    # Get current option prices
    async with OptionsService() as svc:
        chain_by_symbol = {}
        items = []

        for pos in positions:
            expiry_str = pos.expiry_date.strftime("%Y-%m-%d") if isinstance(pos.expiry_date, datetime) else str(pos.expiry_date)
            key = (pos.underlying_symbol, expiry_str)
            if key not in chain_by_symbol:
                chain = await svc.get_options_chain(pos.underlying_symbol, expiry=expiry_str, strike_count=5)
                chain_by_symbol[key] = chain

            chain_data = chain_by_symbol.get(key)
            current_price = None
            if chain_data:
                for q in chain_data.calls + chain_data.puts:
                    if abs(q.strike - float(pos.strike_price)) < 0.01 and q.option_type == pos.option_type:
                        current_price = (q.bid + q.ask) / 2 if q.bid and q.ask else q.last_price
                        break

            market_value = current_price * pos.quantity if current_price else None
            cost_basis = pos.premium * pos.quantity
            unrealized_pnl = market_value - cost_basis if market_value else None
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if unrealized_pnl and cost_basis else None

            close_date_str = pos.close_date.strftime("%Y-%m-%d") if pos.close_date else None

            items.append(OptionPositionSchema(
                id=str(pos.id),
                underlying_symbol=pos.underlying_symbol,
                strike_price=float(pos.strike_price),
                expiry_date=expiry_str,
                option_type=pos.option_type,
                quantity=float(pos.quantity),
                premium=float(pos.premium),
                open_date=pos.open_date.strftime("%Y-%m-%d") if isinstance(pos.open_date, datetime) else str(pos.open_date),
                close_date=close_date_str,
                is_closed=pos.is_closed,
                notes=pos.notes,
                current_price=current_price,
                market_value=market_value,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_pct=unrealized_pnl_pct,
            ))

        return items


@router.post("/portfolio/positions", response_model=OptionPositionSchema)
async def add_option_position(
    position: OptionPositionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a new option position to portfolio.
    """
    expiry_dt = datetime.strptime(position.expiry_date, "%Y-%m-%d")

    db_pos = OptionPosition(
        user_id=user.id,
        underlying_symbol=position.underlying_symbol.upper(),
        strike_price=position.premium,  # actually premium per share
        expiry_date=expiry_dt,
        option_type=position.option_type,
        quantity=position.quantity,
        premium=position.premium,
        open_date=datetime.utcnow(),
        notes=position.notes,
    )
    # Fix: strike_price should be strike, not premium
    db_pos.strike_price = position.strike_price

    db.add(db_pos)
    await db.commit()
    await db.refresh(db_pos)

    expiry_str = db_pos.expiry_date.strftime("%Y-%m-%d")
    return OptionPositionSchema(
        id=str(db_pos.id),
        underlying_symbol=db_pos.underlying_symbol,
        strike_price=float(db_pos.strike_price),
        expiry_date=expiry_str,
        option_type=db_pos.option_type,
        quantity=float(db_pos.quantity),
        premium=float(db_pos.premium),
        open_date=db_pos.open_date.strftime("%Y-%m-%d"),
        close_date=None,
        is_closed=False,
        notes=db_pos.notes,
    )


@router.delete("/portfolio/positions/{position_id}")
async def close_option_position(
    position_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Close (mark as closed) an option position.
    """
    result = await db.execute(
        select(OptionPosition).where(
            OptionPosition.id == position_id,
            OptionPosition.user_id == user.id,
        )
    )
    pos = result.scalar_one_or_none()
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")

    pos.is_closed = True
    pos.close_date = datetime.utcnow()
    await db.commit()

    return {"message": "Position closed successfully", "id": str(pos.id)}

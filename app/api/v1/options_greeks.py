"""
Options Greeks & Strategy Analysis API
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.options import OptionContract, OptionPosition
from app.services.options_greeks_service import OptionsGreeksService


router = APIRouter(prefix="/options-greeks", tags=["options-greeks"])


class GreeksRequest(BaseModel):
    symbol: str
    strike_price: float
    expiry_date: str
    option_type: str  # CALL or PUT
    current_price: float
    volatility: Optional[float] = 0.25
    risk_free_rate: Optional[float] = 0.05


class StrategyPosition(BaseModel):
    strike: float
    premium: float
    type: str  # CALL or PUT
    quantity: int = 1


class StrategyAnalysisRequest(BaseModel):
    strategy_type: str
    positions: list[StrategyPosition]
    underlying_price: float


class PayoffDataRequest(BaseModel):
    strategy_type: str
    underlying_price: float
    strikes: list[float]
    premiums: list[float]
    option_types: list[str]
    quantities: list[int]


class GreeksResponse(BaseModel):
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    theoretical_price: float


class PortfolioGreeksResponse(BaseModel):
    delta: float
    gamma: float
    theta: float
    vega: float


@router.post("/calculate", response_model=GreeksResponse)
def calculate_greeks(request: GreeksRequest, db: Session = Depends(get_db)):
    """
    Calculate Greeks and theoretical price for an option.
    """
    try:
        expiry = datetime.fromisoformat(request.expiry_date.replace("Z", "+00:00"))
        T = max((expiry - datetime.now()).days / 365, 0)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid expiry_date format")

    service = OptionsGreeksService(db)

    # Calculate T in years
    expiry_dt = expiry if expiry.tzinfo else datetime.fromisoformat(request.expiry_date)
    T = max((expiry_dt - datetime.now()).days / 365, 0)

    greeks = service.calculate_greeks(
        S=request.current_price,
        K=request.strike_price,
        T=T,
        r=request.risk_free_rate,
        sigma=request.volatility,
        option_type=request.option_type
    )

    theoretical_price = service.black_scholes_price(
        S=request.current_price,
        K=request.strike_price,
        T=T,
        r=request.risk_free_rate,
        sigma=request.volatility,
        option_type=request.option_type
    )

    return GreeksResponse(
        **greeks,
        theoretical_price=round(theoretical_price, 2)
    )


@router.get("/iv/{symbol}", response_model=dict)
def calculate_implied_volatility(
    symbol: str,
    strike_price: float = Query(...),
    expiry_date: str = Query(...),
    option_type: str = Query(...),
    market_price: float = Query(...),
    current_price: float = Query(...),
    risk_free_rate: float = Query(0.05),
    db: Session = Depends(get_db)
):
    """
    Calculate implied volatility for an option contract.
    """
    try:
        expiry = datetime.fromisoformat(expiry_date.replace("Z", "+00:00"))
        T = max((expiry - datetime.now()).days / 365, 0)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid expiry_date format")

    service = OptionsGreeksService(db)

    iv = service.calculate_implied_volatility(
        market_price=market_price,
        S=current_price,
        K=strike_price,
        T=T,
        r=risk_free_rate,
        option_type=option_type
    )

    if iv is None:
        raise HTTPException(status_code=400, detail="Could not calculate implied volatility")

    return {
        "symbol": symbol,
        "strike_price": strike_price,
        "expiry_date": expiry_date,
        "option_type": option_type,
        "implied_volatility": round(iv * 100, 2),  # As percentage
        "market_price": market_price,
        "current_price": current_price
    }


@router.get("/portfolio/{user_id}", response_model=PortfolioGreeksResponse)
def get_portfolio_greeks(
    user_id: UUID,
    current_prices: str = Query(..., description="Comma-separated symbol:price pairs, e.g., AAPL:150,TSLA:200"),
    db: Session = Depends(get_db)
):
    """
    Calculate aggregate Greeks for all user option positions.
    """
    prices = {}
    for pair in current_prices.split(","):
        if ":" in pair:
            symbol, price = pair.split(":")
            prices[symbol.strip().upper()] = float(price)

    if not prices:
        raise HTTPException(status_code=400, detail="No valid price data provided")

    service = OptionsGreeksService(db)
    greeks = service.calculate_portfolio_greeks(str(user_id), prices)

    return PortfolioGreeksResponse(**greeks)


@router.post("/strategy/analyze")
def analyze_strategy(request: StrategyAnalysisRequest, db: Session = Depends(get_db)):
    """
    Analyze an options strategy (Covered Call, Bull Spread, etc.).
    """
    valid_strategies = [
        "COVERED_CALL", "PROTECTIVE_PUT", "COLLAR",
        "BULL_SPREAD", "BEAR_SPREAD", "STRADDLE", "STRANGLE",
        "BUTTERFLY", "IRON_CONDOR", "IRON_BUTTERFLY"
    ]

    if request.strategy_type not in valid_strategies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy. Must be one of: {', '.join(valid_strategies)}"
        )

    service = OptionsGreeksService(db)

    positions = [p.model_dump() for p in request.positions]
    analysis = service.analyze_strategy(
        strategy_type=request.strategy_type,
        positions=positions,
        current_price=request.underlying_price
    )

    return analysis


@router.post("/strategy/payoff-data")
def get_strategy_payoff_data(request: PayoffDataRequest, db: Session = Depends(get_db)):
    """
    Generate payoff diagram data for a strategy (for charting).
    """
    if len(request.strikes) != len(request.premiums) != len(request.option_types) != len(request.quantities):
        raise HTTPException(status_code=400, detail="All input arrays must have the same length")

    service = OptionsGreeksService(db)

    data = service.get_strategy_payoff_data(
        strategy_type=request.strategy_type,
        underlying_price=request.underlying_price,
        strikes=request.strikes,
        premiums=request.premiums,
        option_types=request.option_types,
        quantities=request.quantities
    )

    return data

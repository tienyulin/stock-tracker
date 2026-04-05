"""
Options API Endpoints
"""

import httpx
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.services.options_service import OptionsService, OptionsChain, GreekLetters


router = APIRouter(prefix="/options", tags=["options"])

_options_service: Optional[OptionsService] = None


def get_options_service() -> OptionsService:
    global _options_service
    if _options_service is None:
        _options_service = OptionsService()
    return _options_service


class OptionQuoteResponse(BaseModel):
    symbol: str
    strike: float
    expiry: str
    option_type: str
    last_price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    implied_volatility: float
    intrinsic_value: float
    moneyness: str


class OptionsChainResponse(BaseModel):
    symbol: str
    underlying_price: float
    timestamp: int
    calls: list[OptionQuoteResponse]
    puts: list[OptionQuoteResponse]


class GreekLettersResponse(BaseModel):
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


@router.get("/{symbol}", response_model=OptionsChainResponse)
async def get_options_chain(
    symbol: str,
    expiry: Optional[str] = Query(None, description="Expiry date YYYY-MM-DD"),
    service: OptionsService = Depends(get_options_service),
):
    """
    Get options chain for a symbol.

    Returns calls and puts with strike, price, IV, volume, etc.
    """
    try:
        chain = await service.get_options_chain(symbol, expiry)
        return OptionsChainResponse(
            symbol=chain.symbol,
            underlying_price=chain.underlying_price,
            timestamp=chain.timestamp,
            calls=[OptionQuoteResponse(**c.__dict__) for c in chain.calls],
            puts=[OptionQuoteResponse(**p.__dict__) for p in chain.puts],
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        raise HTTPException(status_code=502, detail="Upstream data provider error")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/greeks", response_model=GreekLettersResponse)
async def get_greeks(
    symbol: str,
    strike: float = Query(..., description="Strike price"),
    expiry: str = Query(..., description="Expiry date YYYY-MM-DD"),
    option_type: str = Query(..., regex="^(call|put)$"),
    service: OptionsService = Depends(get_options_service),
):
    """
    Calculate Greek letters (Delta, Gamma, Theta, Vega, Rho) for an option.

    Uses Black-Scholes model with implied volatility from Yahoo Finance.
    """
    try:
        greeks = await service.calculate_greeks(symbol, strike, expiry, option_type)
        return GreekLettersResponse(**greeks.__dict__)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

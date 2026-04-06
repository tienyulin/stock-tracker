"""
Foreign Exchange & FX Risk Management API
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.services.fx_service import FXService


router = APIRouter(prefix="/fx", tags=["fx"])


# Request/Response Models
class FXConversionRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str


class FXConversionResponse(BaseModel):
    original_amount: float
    converted_amount: float
    from_currency: str
    to_currency: str
    exchange_rate: float


class FXPositionItem(BaseModel):
    currency: str
    value: float
    asset_type: Optional[str] = None


class FXHedgeRequest(BaseModel):
    assets: list[FXPositionItem]
    liabilities: list[FXPositionItem]
    base_currency: str = "USD"


class FXSensitivityRequest(BaseModel):
    positions: list[FXPositionItem]
    base_currency: str = "USD"
    volatility_pct: float = 0.05


class FXHedgingCostRequest(BaseModel):
    notional_amount: float
    hedging_ratio: float
    forward_rate: float
    spot_rate: float
    tenor_days: int


class FXAlertRequest(BaseModel):
    base_currency: str
    target_currency: str
    target_rate: float
    alert_type: str  # RATE_ABOVE, RATE_BELOW


# Endpoints
@router.get("/rates/{from_currency}/{to_currency}", response_model=dict)
async def get_exchange_rate(
    from_currency: str,
    to_currency: str
):
    """
    Get current exchange rate between two currencies.
    """
    if from_currency not in FXService.SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported currency: {from_currency}. Supported: {', '.join(FXService.SUPPORTED_CURRENCIES)}"
        )
    if to_currency not in FXService.SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported currency: {to_currency}. Supported: {', '.join(FXService.SUPPORTED_CURRENCIES)}"
        )

    service = FXService()
    rate = await service.get_exchange_rate(from_currency.upper(), to_currency.upper())

    return {
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "rate": round(rate, 6),
        "timestamp": "now"
    }


@router.post("/convert", response_model=FXConversionResponse)
async def convert_currency(request: FXConversionRequest):
    """
    Convert an amount from one currency to another.
    """
    if request.from_currency not in FXService.SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {request.from_currency}")
    if request.to_currency not in FXService.SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {request.to_currency}")

    service = FXService()
    rate = await service.get_exchange_rate(request.from_currency.upper(), request.to_currency.upper())
    converted = await service.convert_amount(request.amount, request.from_currency.upper(), request.to_currency.upper())

    return FXConversionResponse(
        original_amount=request.amount,
        converted_amount=round(converted, 2),
        from_currency=request.from_currency.upper(),
        to_currency=request.to_currency.upper(),
        exchange_rate=round(rate, 6)
    )


@router.post("/sensitivity")
async def calculate_fx_sensitivity(request: FXSensitivityRequest):
    """
    Calculate FX sensitivity (VaR-like exposure) for a portfolio.
    """
    service = FXService()
    positions = [p.model_dump() for p in request.positions]
    result = service.calculate_fx_sensitivity(positions, request.base_currency, request.volatility_pct)
    return result


@router.post("/natural-hedge")
async def calculate_natural_hedge(request: FXHedgeRequest):
    """
    Calculate natural hedge between assets and liabilities in same currency.
    """
    service = FXService()
    assets = [a.model_dump() for a in request.assets]
    liabilities = [liability.model_dump() for liability in request.liabilities]
    result = service.calculate_natural_hedge(assets, liabilities, request.base_currency)
    return result


@router.post("/hedging-cost")
async def calculate_hedging_cost(request: FXHedgingCostRequest):
    """
    Calculate cost of hedging using forward contract.
    """
    if request.hedging_ratio < 0 or request.hedging_ratio > 1:
        raise HTTPException(status_code=400, detail="hedging_ratio must be between 0 and 1")
    if request.tenor_days <= 0:
        raise HTTPException(status_code=400, detail="tenor_days must be positive")

    service = FXService()
    result = service.calculate_hedging_cost(
        notional_amount=request.notional_amount,
        hedging_ratio=request.hedging_ratio,
        forward_rate=request.forward_rate,
        spot_rate=request.spot_rate,
        tenor_days=request.tenor_days
    )
    return result


@router.post("/allocation")
async def get_currency_allocation(
    request: FXHedgeRequest,
):
    """
    Get currency allocation breakdown for a portfolio.
    """
    service = FXService()
    assets = [a.model_dump() for a in request.assets]
    result = await service.get_currency_allocation(assets, request.base_currency)
    return result


@router.get("/currencies")
async def list_supported_currencies():
    """
    List all supported currencies.
    """
    return {
        "currencies": FXService.SUPPORTED_CURRENCIES,
        "count": len(FXService.SUPPORTED_CURRENCIES)
    }


@router.get("/portfolio/{user_id}/fx-exposure")
async def get_portfolio_fx_exposure(
    user_id: UUID,
    base_currency: str = Query("USD"),
    volatility_pct: float = Query(0.05, ge=0, le=1)
):
    """
    Get FX exposure summary for a user's portfolio.
    """
    # In production, would fetch user's actual positions from database
    return {
        "user_id": str(user_id),
        "base_currency": base_currency,
        "volatility_assumption": f"{volatility_pct * 100}%",
        "message": "Connect to user's portfolio positions for actual FX exposure calculation"
    }

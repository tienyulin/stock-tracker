"""
Pydantic schemas for commodities & precious metals.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ─── Commodity Position Schemas ─────────────────────────────────────────────

class CommodityPositionCreate(BaseModel):
    """Schema for creating a commodity position."""

    name: str = Field(..., min_length=1, max_length=255)
    commodity_type: str = Field(..., pattern="^(gold|silver|platinum|oil|natural_gas|agricultural|other)$")
    ticker: Optional[str] = Field(None, max_length=20)
    quantity: float = Field(..., gt=0)
    unit: str = Field(default="shares", max_length=20)
    purchase_price: float = Field(..., gt=0)
    current_price: Optional[float] = Field(None, gt=0)
    purchase_date: date
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class CommodityPositionUpdate(BaseModel):
    """Schema for updating a commodity position."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    commodity_type: Optional[str] = Field(None, pattern="^(gold|silver|platinum|oil|natural_gas|agricultural|other)$")
    ticker: Optional[str] = Field(None, max_length=20)
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = Field(None, max_length=20)
    purchase_price: Optional[float] = Field(None, gt=0)
    current_price: Optional[float] = Field(None, gt=0)
    purchase_date: Optional[date] = None
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None


class CommodityPositionResponse(BaseModel):
    """Response schema for a commodity position."""

    id: UUID
    user_id: UUID
    name: str
    commodity_type: str
    ticker: Optional[str]
    quantity: float
    unit: str
    purchase_price: float
    current_price: Optional[float]
    market_value: Optional[float]
    unrealized_pnl: Optional[float]
    purchase_date: date
    currency: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommoditySummaryResponse(BaseModel):
    """Summary statistics for all commodity positions."""

    total_positions: int
    total_market_value: float
    total_unrealized_pnl: float
    by_type: dict[str, dict]


class SyncPricesResponse(BaseModel):
    """Response for price sync operation."""

    updated: list[dict]
    errors: list[dict]


# ─── Futures Contract Schemas ────────────────────────────────────────────────

class FuturesContractCreate(BaseModel):
    """Schema for creating a futures contract."""

    name: str = Field(..., min_length=1, max_length=255)
    commodity_type: str = Field(..., pattern="^(gold|silver|platinum|oil|natural_gas|agricultural|other)$")
    ticker: Optional[str] = Field(None, max_length=20)
    contract_size: float = Field(..., gt=0)
    contract_month: str = Field(..., max_length=10)  # e.g. "2026-06"
    expiration_date: date
    entry_price: float = Field(..., gt=0)
    position_type: str = Field(default="long", pattern="^(long|short)$")
    margin_required: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None


class FuturesContractUpdate(BaseModel):
    """Schema for updating a futures contract."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    commodity_type: Optional[str] = Field(None, pattern="^(gold|silver|platinum|oil|natural_gas|agricultural|other)$")
    ticker: Optional[str] = Field(None, max_length=20)
    contract_size: Optional[float] = Field(None, gt=0)
    contract_month: Optional[str] = Field(None, max_length=10)
    expiration_date: Optional[date] = None
    entry_price: Optional[float] = Field(None, gt=0)
    current_price: Optional[float] = Field(None, gt=0)
    position_type: Optional[str] = Field(None, pattern="^(long|short)$")
    margin_required: Optional[float] = Field(None, gt=0)
    realized_pnl: Optional[float] = None
    notes: Optional[str] = None


class FuturesContractResponse(BaseModel):
    """Response schema for a futures contract."""

    id: UUID
    user_id: UUID
    name: str
    commodity_type: str
    ticker: Optional[str]
    contract_size: float
    contract_month: str
    expiration_date: date
    position_type: str
    entry_price: float
    current_price: Optional[float]
    market_value: Optional[float]
    margin_required: Optional[float]
    realized_pnl: Optional[float]
    unrealized_pnl: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FuturesSummaryResponse(BaseModel):
    """Summary for futures contracts."""

    total_contracts: int
    total_market_value: float
    total_unrealized_pnl: float
    total_margin_required: float


class ExpirationAlertResponse(BaseModel):
    """Response for expiration alerts."""

    id: str
    name: str
    commodity_type: str
    contract_month: str
    expiration_date: str
    days_until_expiration: int
    position_type: str
    entry_price: float
    current_price: Optional[float]
    unrealized_pnl: Optional[float]


# ─── Precious Metals Schemas ────────────────────────────────────────────────

class PreciousMetalsPricesResponse(BaseModel):
    """Current prices for precious metals."""

    gold: Optional[float]
    silver: Optional[float]
    platinum: Optional[float]


class HistoricalDataResponse(BaseModel):
    """Historical price data for a commodity."""

    metal: str
    data: list[dict]


class InflationHedgeMetricsResponse(BaseModel):
    """Inflation hedge analysis."""

    gold_price: Optional[float]
    dxy_index: Optional[float]
    tips_price: Optional[float]
    gold_change_1m_pct: Optional[float]
    gold_change_1y_pct: Optional[float]
    inflation_hedge_signal: str

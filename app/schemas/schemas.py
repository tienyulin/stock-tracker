"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Stock schemas
class StockQuoteResponse(BaseModel):
    """Stock quote response."""

    symbol: str
    price: float
    volume: int
    timestamp: Optional[int] = None
    market_state: Optional[str] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None


class StockHistoryResponse(BaseModel):
    """Stock history response."""

    symbol: str
    timestamps: list[int]
    opens: list[float]
    highs: list[float]
    lows: list[float]
    closes: list[float]
    volumes: list[int]


# Watchlist schemas
class WatchlistItemCreate(BaseModel):
    """Schema for creating a watchlist item."""

    symbol: str = Field(..., min_length=1, max_length=20)
    notes: Optional[str] = None


class WatchlistItemResponse(BaseModel):
    """Watchlist item response."""

    id: UUID
    symbol: str
    notes: Optional[str]
    added_at: datetime

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    """Schema for creating a watchlist."""

    name: str = Field(..., min_length=1, max_length=200)
    is_default: bool = False


class WatchlistUpdate(BaseModel):
    """Schema for updating a watchlist."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    is_default: Optional[bool] = None


class WatchlistResponse(BaseModel):
    """Watchlist response."""

    id: UUID
    name: str
    is_default: bool
    items: list[WatchlistItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Alert schemas
class AlertCreate(BaseModel):
    """Schema for creating an alert."""

    symbol: str = Field(..., min_length=1, max_length=20)
    condition_type: str = Field(..., pattern="^(above|below|change_pct)$")
    threshold: float


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""

    is_active: Optional[bool] = None
    condition_type: Optional[str] = Field(None, pattern="^(above|below|change_pct)$")
    threshold: Optional[float] = None
    triggered_at: Optional[int] = None  # Set to null to reset triggered state


class AlertResponse(BaseModel):
    """Alert response."""

    id: UUID
    symbol: str
    condition_type: str
    threshold: float
    is_active: bool
    triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Health check
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    timestamp: datetime

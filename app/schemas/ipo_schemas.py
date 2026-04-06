"""
Pydantic schemas for IPO tracking.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.ipo import IPOAlertType, IPOStatus


class IPOCreate(BaseModel):
    company_name: str
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    ipo_price_min: Optional[float] = None
    ipo_price_max: Optional[float] = None
    final_ipo_price: Optional[float] = None
    shares_offered: Optional[float] = None
    lot_size: Optional[int] = None
    oversubscription_ratio: Optional[float] = None
    application_deadline: Optional[datetime] = None
    listing_date: Optional[datetime] = None
    first_trading_date: Optional[datetime] = None
    underwriter: Optional[str] = None
    status: str = Field(default=IPOStatus.UPCOMING.value)
    estimated_market_cap: Optional[float] = None
    raising_amount: Optional[float] = None
    notes: Optional[str] = None


class IPOUpdate(BaseModel):
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    ipo_price_min: Optional[float] = None
    ipo_price_max: Optional[float] = None
    final_ipo_price: Optional[float] = None
    shares_offered: Optional[float] = None
    lot_size: Optional[int] = None
    oversubscription_ratio: Optional[float] = None
    application_deadline: Optional[datetime] = None
    listing_date: Optional[datetime] = None
    first_trading_date: Optional[datetime] = None
    underwriter: Optional[str] = None
    status: Optional[str] = None
    estimated_market_cap: Optional[float] = None
    raising_amount: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class IPOResponse(BaseModel):
    id: str
    user_id: str
    company_name: str
    ticker: Optional[str]
    exchange: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    ipo_price_min: Optional[float]
    ipo_price_max: Optional[float]
    final_ipo_price: Optional[float]
    shares_offered: Optional[float]
    lot_size: Optional[int]
    oversubscription_ratio: Optional[float]
    application_deadline: Optional[datetime]
    listing_date: Optional[datetime]
    first_trading_date: Optional[datetime]
    underwriter: Optional[str]
    status: str
    estimated_market_cap: Optional[float]
    raising_amount: Optional[float]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IPOAlertCreate(BaseModel):
    ipo_id: str
    alert_type: str = Field(default=IPOAlertType.DEADLINE.value)
    message: Optional[str] = None


class IPOAlertResponse(BaseModel):
    id: str
    user_id: str
    ipo_id: str
    alert_type: str
    is_active: bool
    triggered_at: Optional[datetime]
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class IPOAnalysisResponse(BaseModel):
    ipo_id: str
    company_name: str
    valuation_range: dict
    underwriter_info: Optional[dict]
    peer_comparison: Optional[list]
    risk_factors: Optional[list]


class IPOCalendarResponse(BaseModel):
    upcoming_ipos: list[IPOResponse]
    deadlines: list[dict]
    first_day_stats: Optional[dict]

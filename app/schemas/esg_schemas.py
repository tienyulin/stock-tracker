"""
Pydantic schemas for ESG & Sustainable Investing.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ─── ESG Score Schemas ───────────────────────────────────────────────────────

class EsgScoreCreate(BaseModel):
    """Schema for creating an ESG score entry."""

    ticker: str = Field(..., min_length=1, max_length=20)
    company_name: str = Field(..., min_length=1, max_length=255)
    esg_total_score: float = Field(..., ge=0, le=100)
    environmental_score: float = Field(..., ge=0, le=100)
    social_score: float = Field(..., ge=0, le=100)
    governance_score: float = Field(..., ge=0, le=100)
    carbon_footprint_tons: Optional[float] = Field(None, ge=0)
    water_usage_m3: Optional[float] = Field(None, ge=0)
    waste_tons: Optional[float] = Field(None, ge=0)
    data_source: str = Field(default="msci", max_length=50)
    rating_date: date


class EsgScoreResponse(BaseModel):
    """Response schema for an ESG score."""

    id: UUID
    user_id: UUID
    ticker: str
    company_name: str
    esg_total_score: float
    environmental_score: float
    social_score: float
    governance_score: float
    carbon_footprint_tons: Optional[float] = None
    water_usage_m3: Optional[float] = None
    waste_tons: Optional[float] = None
    data_source: str
    rating_date: date
    last_updated: datetime

    class Config:
        from_attributes = True


class PortfolioEsgSummary(BaseModel):
    """Portfolio-level ESG summary."""

    portfolio_esg_score: float
    portfolio_env_score: float
    portfolio_social_score: float
    portfolio_gov_score: float
    total_carbon_tons: float
    total_water_m3: float
    total_waste_tons: float
    holdings_count: int
    screened_count: int
    esg_rating_distribution: dict[str, int]  # e.g. {"AAA": 3, "BB": 5}


class EsgTrendResponse(BaseModel):
    """Monthly ESG trend data point."""

    month: date
    esg_total_score: float
    environmental_score: float
    social_score: float
    governance_score: float


class CarbonFootprintResponse(BaseModel):
    """Carbon footprint analysis."""

    ticker: str
    company_name: str
    carbon_tons: float
    carbon_intensity_per_revenue: Optional[float] = None
    benchmark_comparison: Optional[str] = None  # below/above average
    percentile_rank: Optional[int] = None  # 1-100


class PortfolioCarbonResponse(BaseModel):
    """Portfolio-wide carbon footprint."""

    total_carbon_tons: float
    carbon_by_sector: dict[str, float]
    benchmark_average_tons: float
    vs_benchmark_pct: float  # positive = above benchmark
    highest_carbon_ticker: str
    lowest_carbon_ticker: str


# ─── Controversy Alert Schemas ───────────────────────────────────────────────

class ControversyAlertResponse(BaseModel):
    """Response schema for a controversy alert."""

    id: UUID
    user_id: UUID
    ticker: str
    company_name: str
    controversy_type: str
    severity: str
    headline: str
    description: Optional[str] = None
    source_url: Optional[str] = None
    alert_date: date
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ControversyCheckResponse(BaseModel):
    """Response for controversy check."""

    ticker: str
    has_controversies: bool
    alerts: list[ControversyAlertResponse]


# ─── Exclusion List Schemas ─────────────────────────────────────────────────

class ExclusionListCreate(BaseModel):
    """Schema for creating an exclusion list entry."""

    list_type: str = Field(..., pattern="^(negative_screening|ethical_exclusion)$")
    sector: Optional[str] = Field(None, max_length=100)
    ticker: Optional[str] = Field(None, max_length=20)
    company_name: Optional[str] = Field(None, max_length=255)
    reason: Optional[str] = None


class ExclusionListUpdate(BaseModel):
    """Schema for updating an exclusion list entry."""

    list_type: Optional[str] = Field(None, pattern="^(negative_screening|ethical_exclusion)$")
    sector: Optional[str] = Field(None, max_length=100)
    ticker: Optional[str] = Field(None, max_length=20)
    company_name: Optional[str] = Field(None, max_length=255)
    reason: Optional[str] = None
    is_active: Optional[bool] = None


class ExclusionListResponse(BaseModel):
    """Response schema for an exclusion list entry."""

    id: UUID
    user_id: UUID
    list_type: str
    sector: Optional[str] = None
    ticker: Optional[str] = None
    company_name: Optional[str] = None
    reason: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── ESG Alternatives Schemas ────────────────────────────────────────────────

class SustainableAlternativeResponse(BaseModel):
    """Sustainable alternative recommendation."""

    original_ticker: str
    original_esg_score: float
    alternative_ticker: str
    alternative_name: str
    alternative_esg_score: float
    sector: str
    reason: str


class PortfolioScreenResponse(BaseModel):
    """Result of portfolio screening."""

    total_holdings: int
    flagged_holdings: list[dict]
    screened_holdings: list[dict]
    compliance_score: float  # 0-100
    excluded_value: float

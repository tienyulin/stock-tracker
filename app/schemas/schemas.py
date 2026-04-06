"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
import uuid
from uuid import UUID

from pydantic import BaseModel, Field


# Stock schemas
class StockQuoteResponse(BaseModel):
    """Stock quote response."""

    symbol: str
    name: Optional[str] = None
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


# Auth schemas
class UserCreate(BaseModel):
    """Schema for user registration."""

    email: str = Field(..., min_length=5, max_length=255)
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """Schema for user response."""

    id: str
    email: str
    username: str
    created_at: Optional[str] = None


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str = "bearer"
    user_id: str


# AI Chat schemas
class AIChatMessage(BaseModel):
    """Schema for a single chat message."""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class AIChatRequest(BaseModel):
    """Schema for AI chat request."""

    message: str = Field(..., min_length=1, max_length=4000)
    conversation_history: list[AIChatMessage] = Field(default_factory=list)


class AIChatResponse(BaseModel):
    """Schema for AI chat response."""

    response: str
    conversation_id: Optional[uuid.UUID] = None
    disclaimer: str = "This is not financial advice. Always do your own research."


# Monte Carlo Retirement Simulation schemas
class RetirementSimulationRequest(BaseModel):
    """Schema for Monte Carlo retirement simulation request."""

    current_age: int = Field(..., ge=18, le=80)
    retirement_age: int = Field(..., ge=19, le=90)
    current_savings: float = Field(..., ge=0)
    monthly_contribution: float = Field(..., ge=0)
    desired_monthly_income: float = Field(..., ge=0)
    portfolio_allocation: dict[str, float] = Field(
        default_factory=lambda: {"stocks": 0.7, "bonds": 0.2, "cash": 0.1}
    )
    num_simulations: int = Field(default=1000, ge=100, le=10000)
    years_to_simulate: Optional[int] = Field(default=None, ge=1, le=50)


class SimulationOutcome(BaseModel):
    """Single simulation outcome."""

    final_portfolio_value: float
    total_contributions: float
    total_growth: float
    monthly_income_sustainable: bool


class RetirementSimulationResponse(BaseModel):
    """Schema for Monte Carlo retirement simulation response."""

    success_probability: float  # 0.0 to 1.0
    median_outcome: float
    percentile_10: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    average_outcome: float
    worst_outcome: float
    best_outcome: float
    total_simulations: int
    years_until_retirement: int
    assumptions: dict[str, float]


# Dividend schemas
class DividendPaymentCreate(BaseModel):
    """Schema for creating a dividend payment record."""

    symbol: str = Field(..., min_length=1, max_length=20)
    ex_dividend_date: datetime
    payment_date: datetime
    amount_per_share: float = Field(..., ge=0)
    shares_owned: float = Field(default=0, ge=0)
    total_amount: Optional[float] = None  # Auto-calculated if not provided
    currency: str = Field(default="USD", max_length=3)


class DividendPaymentResponse(BaseModel):
    """Response schema for a dividend payment."""

    id: UUID
    symbol: str
    ex_dividend_date: datetime
    payment_date: datetime
    amount_per_share: float
    shares_owned: float
    total_amount: float
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class DividendHoldingUpdate(BaseModel):
    """Schema for updating dividend holding information."""

    shares_owned: Optional[float] = Field(None, ge=0)
    cost_basis: Optional[float] = Field(None, ge=0)
    annual_dividend: Optional[float] = Field(None, ge=0)


class DividendHoldingResponse(BaseModel):
    """Response schema for a dividend holding."""

    id: UUID
    symbol: str
    shares_owned: float
    cost_basis: float
    annual_dividend: float
    dividend_yield: float
    yield_on_cost: float
    last_dividend_date: Optional[datetime]
    dividend_growth_rate: float
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class DividendCalendarEntry(BaseModel):
    """Schema for an upcoming dividend date entry."""

    symbol: str
    ex_dividend_date: datetime
    payment_date: datetime
    amount_per_share: float


class DividendDashboardResponse(BaseModel):
    """Response schema for dividend dashboard."""

    total_dividends_received: float
    dividends_this_year: float
    dividends_last_year: float
    year_over_year_growth: float
    portfolio_dividend_yield: float
    yield_on_cost: float
    recent_payments: list[DividendPaymentResponse]
    upcoming_ex_dividends: list[DividendCalendarEntry]


class DividendGrowthResponse(BaseModel):
    """Response schema for dividend growth analytics."""

    symbol: str
    annual_dividend: float
    previous_annual_dividend: float
    dividend_growth_rate: float
    yield_on_cost: float
    current_yield: float
    years_of_growth: int


# ─── Passive Income Schemas ───────────────────────────────────────────────────


class PassiveIncomeSourceCreate(BaseModel):
    """Schema for creating a passive income source."""

    name: str = Field(..., min_length=1, max_length=200)
    source_type: str = Field(
        ...,
        pattern="^(dividend|rental|interest|royalty|pension|social_security|p2p|other)$",
    )
    description: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)
    expected_monthly_income: float = Field(default=0, ge=0)
    expected_annual_income: float = Field(default=0, ge=0)
    yield_on_cost: Optional[float] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    notes: Optional[str] = None


class PassiveIncomeSourceUpdate(BaseModel):
    """Schema for updating a passive income source."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    source_type: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    expected_monthly_income: Optional[float] = Field(None, ge=0)
    expected_annual_income: Optional[float] = Field(None, ge=0)
    yield_on_cost: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None


class PassiveIncomeSourceResponse(BaseModel):
    """Response schema for a passive income source."""

    id: UUID
    name: str
    source_type: str
    description: Optional[str]
    currency: str
    expected_monthly_income: float
    expected_annual_income: float
    yield_on_cost: Optional[float]
    is_active: bool
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PassiveIncomeRecordCreate(BaseModel):
    """Schema for creating a passive income record."""

    source_id: UUID
    amount: float = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    record_date: datetime
    record_type: str = Field(default="received", pattern="^(received|expected|missed)$")
    notes: Optional[str] = None


class PassiveIncomeRecordResponse(BaseModel):
    """Response schema for a passive income record."""

    id: UUID
    source_id: UUID
    amount: float
    currency: str
    record_date: datetime
    record_type: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PassiveIncomeMonthlySummary(BaseModel):
    """Monthly passive income summary."""

    total: float
    by_type: dict[str, float]
    currency: str


class PassiveIncomeAnnualSummary(BaseModel):
    """Annual passive income summary."""

    year: int
    monthly: list[float]
    total: float
    currency: str


class FireGoalUpsert(BaseModel):
    """Schema for creating/updating a FIRE goal."""

    target_annual_income: float = Field(..., gt=0)
    monthly_expenses: float = Field(..., gt=0)
    target_date: Optional[datetime] = None
    currency: str = Field(default="USD", max_length=3)


class FireGoalResponse(BaseModel):
    """Response schema for a FIRE goal."""

    id: UUID
    target_annual_income: float
    monthly_expenses: float
    target_date: Optional[datetime]
    current_passive_income: float
    progress_percentage: float
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FireProgressResponse(BaseModel):
    """FIRE progress dashboard data."""

    target_annual_income: float
    current_passive_income: float
    progress_percentage: float
    monthly_expenses: float
    monthly_target: float
    months_to_target: int
    target_date: Optional[datetime]
    currency: str


class PassiveIncomeDashboardResponse(BaseModel):
    """Full passive income dashboard response."""

    sources: list[PassiveIncomeSourceResponse]
    monthly_summary: PassiveIncomeMonthlySummary
    annual_summary: PassiveIncomeAnnualSummary
    fire_progress: Optional[FireProgressResponse]

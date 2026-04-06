"""
Data models for cash flow forecasting and liquidity planning.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class IncomeType(str, Enum):
    """Types of income."""
    SALARY = "salary"
    BONUS = "bonus"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    RENTAL = "rental"
    BUSINESS = "business"
    SIDE_HUSTLE = "side_hustle"
    GOVERNMENT_BENEFIT = "government_benefit"
    OTHER_PASSIVE = "other_passive"
    OTHER_ACTIVE = "other_active"


class ExpenseCategory(str, Enum):
    """Categories of expenses."""
    HOUSING = "housing"
    UTILITIES = "utilities"
    FOOD = "food"
    TRANSPORTATION = "transportation"
    HEALTHCARE = "healthcare"
    INSURANCE = "insurance"
    DEBT_PAYMENT = "debt_payment"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    PERSONAL_CARE = "personal_care"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    CHARITY = "charity"
    OTHER = "other"


class LiquidityLevel(str, Enum):
    """Liquidity levels for assets."""
    HIGH = "high"  # Cash, money market
    MEDIUM = "medium"  # Stocks, ETFs
    LOW = "low"  # CDs, bonds, term deposits
    ILLIQUID = "illiquid"  # Real estate, private investments


class CashFlowEntry(BaseModel):
    """Individual cash flow entry."""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    entry_type: str  # "income" or "expense"
    category: str  # IncomeType or ExpenseCategory as string
    amount: Decimal
    date: date
    description: Optional[str] = None
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None  # "monthly", "quarterly", "annual"
    source: Optional[str] = None  # employer name, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MonthlyCashFlow(BaseModel):
    """Monthly aggregated cash flow."""
    year_month: str  # "2026-04"
    total_income: Decimal
    total_expense: Decimal
    net_cash_flow: Decimal
    passive_income: Decimal = Field(default=Decimal("0"))
    active_income: Decimal = Field(default=Decimal("0"))
    income_by_category: dict = Field(default_factory=dict)
    expense_by_category: dict = Field(default_factory=dict)
    savings_rate: float = 0.0  # percentage
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CashFlowForecast(BaseModel):
    """Cash flow forecast for future periods."""
    forecast_months: int  # 3, 6, or 12
    forecasted_entries: list[dict] = Field(default_factory=dict)  # [{month, income, expense, net}]
    expected_balance: Decimal
    shortfall_months: list[str] = Field(default_factory=list)  # months where expenses > income
    confidence_score: float = Field(ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)


class LiquidityPosition(BaseModel):
    """Current liquidity position."""
    total_liquid_assets: Decimal
    high_liquidity: Decimal
    medium_liquidity: Decimal
    low_liquidity: Decimal
    illiquid_assets: Decimal = Field(default=Decimal("0"))
    liquidity_ratio: float = 0.0  # high_liquidity / monthly_expenses
    months_of_expenses_covered: float = 0.0


class EmergencyFundStatus(BaseModel):
    """Emergency fund status."""
    current_emergency_fund: Decimal
    recommended_minimum: Decimal  # 3 months
    recommended_ideal: Decimal  # 6 months
    coverage_months: float  # how many months current fund covers
    shortfall_amount: Decimal  # amount needed to reach ideal
    progress_percentage: float  # 0-100
    is_adequate: bool  # True if >= 3 months


class LargeExpensePlan(BaseModel):
    """Planned large expense."""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    description: str
    estimated_amount: Decimal
    planned_date: date
    months_until: int
    monthly_savings_needed: Decimal
    status: str = "planned"  # planned, in_progress, completed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)

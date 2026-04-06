"""
Pydantic schemas for AI Agent Orchestration.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AgentState(str, Enum):
    """FSM states for the AI agent."""

    IDLE = "IDLE"
    MONITORING = "MONITORING"
    ANALYZING = "ANALYZING"
    RECOMMENDING = "RECOMMENDING"
    ACTING = "ACTING"


class GoalType(str, Enum):
    """Types of financial goals."""

    RETIREMENT = "RETIREMENT"
    HOUSE = "HOUSE"
    EDUCATION = "EDUCATION"
    EMERGENCY_FUND = "EMERGENCY_FUND"
    WEALTH_ACCUMULATION = "WEALTH_ACCUMULATION"
    CUSTOM = "CUSTOM"


class GoalStatus(str, Enum):
    """Status of a financial goal."""

    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    BEHIND = "BEHIND"
    ACHIEVED = "ACHIEVED"
    CANCELLED = "CANCELLED"


class ConnectionStatus(str, Enum):
    """Status of an Open Finance connection."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"
    ERROR = "ERROR"
    PENDING = "PENDING"


class OpenFinanceProvider(str, Enum):
    """Open Finance data providers."""

    ESUN_BANK = "ESUN_BANK"
    YODLEE = "YODLEE"
    PLAID = "PLAID"
    FISCAL_DATA = "FISCAL_DATA"


class GoalDefinition(BaseModel):
    """Definition of a user's financial goal."""

    id: UUID
    user_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    goal_type: GoalType
    target_amount: float = Field(..., ge=0)
    current_amount: float = Field(default=0, ge=0)
    target_date: Optional[date] = None
    monthly_contribution: float = Field(default=0, ge=0)
    status: GoalStatus = GoalStatus.ON_TRACK
    priority: int = Field(default=0, ge=0)  # Higher = more important
    metadata: dict = Field(default_factory=dict)  # Flexible metadata
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GoalProgress(BaseModel):
    """Progress report for a financial goal."""

    goal_id: UUID
    goal_name: str
    goal_type: GoalType
    target_amount: float
    current_amount: float
    target_date: Optional[date]
    progress_percent: float = Field(..., ge=0, le=100)
    monthly_needed: float  # Required monthly contribution to meet goal
    monthly_actual: float  # Actual/average monthly contribution
    on_track: bool
    status: GoalStatus
    projected_completion: Optional[date] = None
    gap_amount: float = 0  # Shortfall if behind
    alerts: list[str] = Field(default_factory=list)
    timestamp: datetime


class HoldingAsset(BaseModel):
    """Normalized asset holding across all accounts."""

    symbol: str
    name: Optional[str] = None
    quantity: float = 0
    current_value: float = 0
    cost_basis: float = 0
    unrealized_gain: float = 0
    unrealized_gain_percent: float = 0
    asset_class: str = "stock"  # stock, bond, cash, real_estate, crypto, other
    account_id: Optional[str] = None  # Source account
    provider: Optional[OpenFinanceProvider] = None


class AccountBalance(BaseModel):
    """Normalized account balance from Open Finance sources."""

    account_id: str
    account_name: str
    account_type: str  # checking, savings, investment, credit, loan
    balance: float
    currency: str = "TWD"
    provider: OpenFinanceProvider
    institution_name: str
    last_updated: datetime


class PersonalFinancialProfile(BaseModel):
    """Comprehensive personal financial profile aggregated from Open Finance."""

    user_id: UUID
    total_net_worth: float = 0
    total_assets: float = 0
    total_liabilities: float = 0
    total_cash: float = 0
    total_investments: float = 0
    total_debt: float = 0
    monthly_income: float = 0
    monthly_expenses: float = 0
    holdings: list[HoldingAsset] = Field(default_factory=list)
    accounts: list[AccountBalance] = Field(default_factory=list)
    credit_score: Optional[int] = None
    risk_tolerance: str = "MODERATE"  # CONSERVATIVE, MODERATE, AGGRESSIVE
    investment_experience: str = "INTERMEDIATE"  # BEGINNER, INTERMEDIATE, ADVANCED
    last_updated: datetime
    connections: list["OpenFinanceConnection"] = Field(default_factory=list)


class OpenFinanceConnection(BaseModel):
    """Connection to an Open Finance data provider."""

    id: UUID
    user_id: UUID
    provider: OpenFinanceProvider
    status: ConnectionStatus
    institution_name: str
    institution_id: str
    account_ids: list[str] = Field(default_factory=list)
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    error_message: Optional[str] = None
    permissions: list[str] = Field(default_factory=list)  # READ_BALANCES, READ_HOLDINGS, etc.
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentAction(BaseModel):
    """An action recommended or taken by the AI agent."""

    action_id: str
    action_type: str  # REBALANCE, TAX_HARVEST, GOAL_ADJUST, ALERT, TRADE
    priority: int = 0  # 1 = critical, 5 = low
    description: str
    rationale: str
    metadata: dict = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0, le=1)
    estimated_impact: Optional[str] = None  # e.g., "$500 tax savings"
    created_at: datetime


class AgentRecommendation(BaseModel):
    """A recommendation generated by the AI agent."""

    recommendation_id: str
    agent_state: AgentState
    category: str  # portfolio_rebalance, tax_loss_harvest, goal_adjustment, etc.
    title: str
    description: str
    actions: list[AgentAction] = Field(default_factory=list)
    priority: int = 0
    confidence: float = Field(default=0.5, ge=0, le=1)
    risk_level: str = "MODERATE"  # LOW, MODERATE, HIGH
    requires_approval: bool = True  # Whether user must approve before acting
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    expires_at: Optional[datetime] = None


class RetirementGapResult(BaseModel):
    """Result of retirement gap calculation."""

    current_savings: float
    required_at_retirement: float
    gap_amount: float
    gap_percentage: float
    success_probability: float
    monthly_shortfall: float
    monthly_surplus: float
    years_to_retirement: int
    recommended_monthly_contribution: float
    assumptions: dict = Field(default_factory=dict)
    simulated_at: datetime


class PortfolioDriftSummary(BaseModel):
    """Summary of portfolio drift analysis."""

    total_value: float
    drift_score: float  # 0-100, higher = more drift from target
    overweight_positions: list[dict] = Field(default_factory=list)
    underweight_positions: list[dict] = Field(default_factory=list)
    rebalancing_trades: list[dict] = Field(default_factory=list)
    estimated_tax_impact: Optional[float] = None
    analyzed_at: datetime


class MonitoringAlert(BaseModel):
    """Alert generated during goal monitoring."""

    alert_id: UUID
    goal_id: Optional[UUID] = None
    alert_type: str  # GOAL_OFF_TRACK, THRESHOLD_BREACH, OPPORTUNITY, RISK
    severity: str  # INFO, WARNING, CRITICAL
    title: str
    message: str
    recommendation: Optional[str] = None
    created_at: datetime
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None


class CoachMessage(BaseModel):
    """A message in the financial coach conversation."""

    message_id: UUID = Field(default_factory=uuid4)
    role: str  # "user" or "coach"
    content: str
    topic: Optional[str] = None  # retirement, investment, budgeting, emergency_fund, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CoachConversation(BaseModel):
    """Financial coach conversation context."""

    user_id: str
    messages: list[CoachMessage] = Field(default_factory=list)
    current_focus: Optional[str] = None  # What the coach is currently addressing
    context_summary: Optional[str] = None  # AI-generated summary of conversation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RetirementReadinessResult(BaseModel):
    """Retirement readiness assessment result."""

    readiness_score: float  # 0-100
    readiness_level: str  # "on_track", "moderate_gap", "significant_gap", "off_track"
    current_nest_egg: float
    on_track_nest_egg: float
    monthly_contribution_needed: float
    years_to_retirement: int
    key_factors: list[str] = Field(default_factory=list)  # e.g., "high_emergency_fund", "diversified_portfolio"
    improvement_suggestions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    assessed_at: datetime = Field(default_factory=datetime.utcnow)


# Update forward references
PersonalFinancialProfile.model_rebuild()

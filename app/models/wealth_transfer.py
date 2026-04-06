"""
Data models for multi-generational wealth transfer and dynasty trust.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class TrustType(str, Enum):
    """Types of trusts."""
    REVOCABLE = "revocable"
    IRREVOCABLE = "irrevocable"
    LIVING = "living"
    TESTAMENTARY = "testamentary"
    GENERATION_SKIPPING = "generation_skipping"
    QUALIFIED_Personal_RESIDence = "qualified_personal_residence"
    CHARITABLE_REMAINDER = "charitable_remainder"
    CHARITABLE_LEAD = "charitable_lead"


class BeneficiaryRelationship(str, Enum):
    """Relationship to grantor."""
    SPOUSE = "spouse"
    CHILD = "child"
    GRANDCHILD = "grandchild"
    SIBLING = "sibling"
    PARENT = "parent"
    OTHER_FAMILY = "other_family"
    CHARITY = "charity"


class TimelineEventType(str, Enum):
    """Types of wealth transfer timeline events."""
    BIRTHDAY = "birthday"
    GRADUATION = "graduation"
    MARRIAGE = "marriage"
    FIRST_HOME = "first_home"
    RETIREMENT = "retirement"
    INHERITANCE = "inheritance"
    ESTATE_TRANSFER = "estate_transfer"
    CHARITABLE_DONATION = "charitable_donation"
    BUSINESS_SUCCESSION = "business_succession"


class EducationFundStatus(str, Enum):
    """Education fund account status."""
    ACTIVE = "active"
    CLOSED = "closed"
    PARTIALLY_WITHDRAWN = "partially_withdrawn"
    FULLY_WITHDRAWN = "fully_withdrawn"


# ============== Education Fund Models ==============

class EducationFund(BaseModel):
    """529 education savings plan account."""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    account_name: str
    account_number_last4: str  # Last 4 digits for reference
    beneficiary_name: str
    beneficiary_relationship: BeneficiaryRelationship
    current_balance: Decimal = Field(default=Decimal("0"))
    total_contributions: Decimal = Field(default=Decimal("0"))
    total_withdrawals: Decimal = Field(default=Decimal("0"))
    target_amount: Decimal
    annual_contribution_limit: Decimal = Field(default=Decimal("18000"))  # 2024 limit
    state: str  # e.g., "NY", "CA"
    plan_name: str
    status: EducationFundStatus = EducationFundStatus.ACTIVE
    projected_college_cost: Optional[Decimal] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EducationFundProgress(BaseModel):
    """Progress tracking for education fund."""
    fund_id: UUID
    current_balance: Decimal
    target_amount: Decimal
    progress_percentage: float  # 0-100
    monthly_contribution: Decimal
    estimated_completion_date: Optional[datetime] = None
    shortfall_amount: Decimal
    years_until_college: int
    inflation_adjusted_target: Decimal


# ============== Trust Models ==============

class Beneficiary(BaseModel):
    """Trust beneficiary."""
    id: UUID = Field(default_factory=uuid4)
    trust_id: UUID
    name: str
    relationship: BeneficiaryRelationship
    date_of_birth: Optional[date] = None
    allocation_percentage: Decimal = Field(ge=Decimal("0"), le=Decimal("100"))
    allocation_amount: Optional[Decimal] = None
    conditions: Optional[str] = None  # e.g., "after age 25"
    is_primary: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TrustAccount(BaseModel):
    """Dynasty trust account."""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    trust_name: str
    trust_type: TrustType
    grantor_name: str
    trustee_name: str
    current_value: Decimal = Field(default=Decimal("0"))
    beneficiaries: list[Beneficiary] = Field(default_factory=list)
    creation_date: date
    termination_date: Optional[date] = None
    trust_terms: Optional[str] = None
    annual_distribution_percentage: Optional[Decimal] = None
    generation_skip_enabled: bool = False
    tax_exempt_enabled: bool = False
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TrustDistributionSchedule(BaseModel):
    """Scheduled distribution from trust."""
    id: UUID = Field(default_factory=uuid4)
    trust_id: UUID
    beneficiary_id: UUID
    scheduled_date: date
    amount: Decimal
    is_distributed: bool = False
    distributed_at: Optional[datetime] = None
    notes: Optional[str] = None


# ============== Wealth Transfer Timeline Models ==============

class WealthTransferEvent(BaseModel):
    """Event on the wealth transfer timeline."""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    event_type: TimelineEventType
    title: str
    description: Optional[str] = None
    event_date: date
    estimated_value: Optional[Decimal] = None
    tax_impact: Optional[Decimal] = None
    related_trust_id: Optional[UUID] = None
    related_education_fund_id: Optional[UUID] = None
    status: str = "planned"  # planned, completed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EstateDistributionPlan(BaseModel):
    """Estate distribution planning."""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    plan_name: str
    total_estate_value: Decimal
    distribution_items: list[dict] = Field(default_factory=list)  # [{beneficiary, asset, amount, percentage}]
    estimated_inheritance_tax: Optional[Decimal] = None
    estimated_estate_tax_rate: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============== Family Constitution Models ==============

class InvestmentPolicyStatement(BaseModel):
    """Family investment policy statement."""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    version: int = 1
    title: str
    purpose: str
    investment_objectives: str
    asset_allocation_targets: dict = Field(default_factory=dict)  # {"stocks": 60, "bonds": 30, "alternatives": 10}
    rebalancing_policy: str
    risk_tolerance: str
    time_horizon: str
    performance_benchmarks: dict = Field(default_factory=dict)
    esg_policy: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FamilyValue(BaseModel):
    """Documented family value."""
    id: UUID = Field(default_factory=uuid4)
    constitution_id: UUID
    category: str  # e.g., "financial", "educational", "philanthropic"
    title: str
    description: str
    priority: int = 1


class FamilyConstitution(BaseModel):
    """Family constitution document."""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    version: int = 1
    title: str = "Family Financial Constitution"
    mission_statement: Optional[str] = None
    core_values: list[str] = Field(default_factory=list)
    investment_policy: Optional[InvestmentPolicyStatement] = None
    family_values: list[FamilyValue] = Field(default_factory=list)
    governance_structure: Optional[str] = None
    succession_plan: Optional[str] = None
    education_resources: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

"""
Tax Optimization API endpoints.
"""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.core.rate_limiter import limiter, DEFAULT_RATE_LIMIT
from app.services.tax_optimization_service import TaxOptimizationService, OptimizationType
from app.services.asset_location_service import AssetLocationService, AccountType, AssetType, Position
from app.services.tax_efficient_withdrawal_service import TaxEfficientWithdrawalService, WithdrawalSource
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/tax-optimization", tags=["Tax Optimization"])


# ─── Pydantic Models ────────────────────────────────────────────────────────────

class PositionInput(BaseModel):
    """Position for tax analysis."""
    symbol: str
    quantity: float
    cost_basis: float
    current_price: float
    purchase_date: str  # YYYY-MM-DD


class TaxSummaryOutput(BaseModel):
    """Tax optimization summary output."""
    total_unrealized_gains: float
    total_unrealized_losses: float
    short_term_unrealized_gains: float
    short_term_unrealized_losses: float
    long_term_unrealized_gains: float
    long_term_unrealized_losses: float
    net_unrealized: float
    harvestable_losses: float
    opportunities_count: int


class OptimizationOpportunityOutput(BaseModel):
    """Single optimization opportunity."""
    type: str
    symbol: str
    description: str
    action: str
    estimated_tax_savings: float
    urgency: str


class LossHarvestingOutput(BaseModel):
    """Loss harvesting candidates output."""
    candidates: list[OptimizationOpportunityOutput]
    total_harvestable_losses: float
    potential_savings: float


class TaxLiabilityInput(BaseModel):
    """Tax liability calculation input."""
    short_term_gains: float = 0.0
    short_term_losses: float = 0.0
    long_term_gains: float = 0.0
    long_term_losses: float = 0.0
    previous_year_carryover: float = 0.0
    filing_status: str = "single"


class TaxLiabilityOutput(BaseModel):
    """Tax liability output."""
    filing_status: str
    short_term_gain: float
    long_term_gain: float
    total_taxable_gain: float
    short_term_tax: float
    long_term_tax: float
    total_tax: float
    net_gain_after_tax: float
    annual_loss_deduction: float
    carryover_remaining: float


class AssetLocationRecommendationInput(BaseModel):
    """Asset location recommendation input."""
    symbol: str
    asset_type: str = Field(default="stock", pattern="^(stock|etf|bond|reit|mutual_fund|money_market|crypto)$")
    quantity: float
    current_price: float
    cost_basis: float
    annual_distribution: float = 0.0
    turnover_rate: float = 0.0
    account_type: str = Field(default="taxable", pattern="^(taxable|traditional_ira|roth_ira|401k|hsa)$")


class AssetLocationOutput(BaseModel):
    """Asset location recommendation output."""
    symbol: str
    current_account: str
    recommended_account: str
    reason: str
    estimated_tax_savings: float
    quantity: float
    priority: str


class WithdrawalStrategyInput(BaseModel):
    """Withdrawal strategy input."""
    current_age: int = Field(ge=18, le=100)
    roth_balance: float = 0.0
    taxable_balance: float = 0.0
    traditional_ira_balance: float = 0.0
    k401k_balance: float = 0.0
    hsa_balance: float = 0.0
    annual_expenses: float = Field(ge=0)
    filing_status: str = "single"
    years_to_plan: int = Field(default=30, ge=5, le=50)
    social_security_annual: float = 0.0


class WithdrawalStepOutput(BaseModel):
    """Single withdrawal step."""
    step_number: int
    source: str
    amount: float
    tax_impact: float
    rationale: str
    cumulative_tax: float


class YearlyWithdrawalOutput(BaseModel):
    """Yearly withdrawal output."""
    year: int
    age: int
    total_withdrawn: float
    total_tax: float
    effective_tax_rate: float
    marginal_tax_rate: float
    rmd_required: float
    steps: list[dict]


class WithdrawalPlanOutput(BaseModel):
    """Complete withdrawal plan."""
    yearly_withdrawals: list[YearlyWithdrawalOutput]
    total_withdrawn: float
    total_taxes_paid: float
    effective_tax_rate: float
    roth_percentage_at_end: float


# ─── Tax Optimization Endpoints ────────────────────────────────────────────────

@router.post("/summary", response_model=TaxSummaryOutput)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_tax_optimization_summary(
    request: Request,
    positions: list[PositionInput],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> TaxSummaryOutput:
    """
    Get tax optimization summary for portfolio.

    Analyzes all positions and identifies:
    - Unrealized gains/losses breakdown
    - Short-term vs long-term positions
    - Harvestable tax losses
    """
    service = TaxOptimizationService()

    pos_dicts = [
        {
            "symbol": p.symbol,
            "quantity": p.quantity,
            "cost_basis": p.cost_basis,
            "current_price": p.current_price,
            "purchase_date": datetime.strptime(p.purchase_date, "%Y-%m-%d"),
        }
        for p in positions
    ]

    summary = service.analyze_portfolio_tax(pos_dicts)

    return TaxSummaryOutput(
        total_unrealized_gains=summary.total_unrealized_gains,
        total_unrealized_losses=summary.total_unrealized_losses,
        short_term_unrealized_gains=summary.short_term_unrealized_gains,
        short_term_unrealized_losses=summary.short_term_unrealized_losses,
        long_term_unrealized_gains=summary.long_term_unrealized_gains,
        long_term_unrealized_losses=summary.long_term_unrealized_losses,
        net_unrealized=summary.net_unrealized,
        harvestable_losses=summary.harvestable_losses,
        opportunities_count=len(summary.opportunities),
    )


@router.post("/opportunities", response_model=list[OptimizationOpportunityOutput])
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_optimization_opportunities(
    request: Request,
    positions: list[PositionInput],
    current_user: Annotated[dict, Depends(get_current_user)],
    opportunity_types: Optional[str] = None,  # comma-separated
) -> list[OptimizationOpportunityOutput]:
    """
    Get all tax optimization opportunities.

    Filters by type if specified (loss_harvest, gain_defer, holding_period, turnover_warning).
    """
    service = TaxOptimizationService()

    pos_dicts = [
        {
            "symbol": p.symbol,
            "quantity": p.quantity,
            "cost_basis": p.cost_basis,
            "current_price": p.current_price,
            "purchase_date": datetime.strptime(p.purchase_date, "%Y-%m-%d"),
        }
        for p in positions
    ]

    summary = service.analyze_portfolio_tax(pos_dicts)

    opportunities = summary.opportunities
    if opportunity_types:
        allowed_types = [t.strip() for t in opportunity_types.split(",")]
        opportunities = [
            o for o in opportunities
            if o.type.value in allowed_types
        ]

    return [
        OptimizationOpportunityOutput(
            type=o.type.value,
            symbol=o.symbol,
            description=o.description,
            action=o.action,
            estimated_tax_savings=o.estimated_tax_savings,
            urgency=o.urgency,
        )
        for o in opportunities
    ]


@router.post("/loss-harvesting", response_model=LossHarvestingOutput)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_loss_harvesting_candidates(
    request: Request,
    positions: list[PositionInput],
    current_user: Annotated[dict, Depends(get_current_user)],
    min_loss: float = 100,
) -> LossHarvestingOutput:
    """
    Get positions with unrealized losses suitable for tax-loss harvesting.

    Only returns positions with losses > min_loss threshold.
    """
    service = TaxOptimizationService()

    pos_dicts = [
        {
            "symbol": p.symbol,
            "quantity": p.quantity,
            "cost_basis": p.cost_basis,
            "current_price": p.current_price,
            "purchase_date": datetime.strptime(p.purchase_date, "%Y-%m-%d"),
        }
        for p in positions
    ]

    candidates = service.get_loss_harvesting_candidates(pos_dicts, min_loss=min_loss)
    total_losses = sum(c.estimated_tax_savings for c in candidates)

    return LossHarvestingOutput(
        candidates=[
            OptimizationOpportunityOutput(
                type=c.type.value,
                symbol=c.symbol,
                description=c.description,
                action=c.action,
                estimated_tax_savings=c.estimated_tax_savings,
                urgency=c.urgency,
            )
            for c in candidates
        ],
        total_harvestable_losses=sum(c.details.get("unrealized_loss", 0) for c in candidates),
        potential_savings=total_losses,
    )


@router.post("/tax-liability", response_model=TaxLiabilityOutput)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def calculate_tax_liability(
    request: Request,
    calc: TaxLiabilityInput,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> TaxLiabilityOutput:
    """
    Calculate estimated tax liability on realized gains/losses.

    Accounts for:
    - Short-term vs long-term gains
    - Loss carryover from previous year
    - Annual $3000 deduction against ordinary income
    """
    service = TaxOptimizationService()
    result = service.calculate_tax_liability(
        realized_gains=calc.short_term_gains + calc.long_term_gains,
        realized_losses=calc.short_term_losses + calc.long_term_losses,
        short_term_gains=calc.short_term_gains,
        long_term_gains=calc.long_term_gains,
        short_term_losses=calc.short_term_losses,
        long_term_losses=calc.long_term_losses,
        previous_year_carryover=calc.previous_year_carryover,
        filing_status=calc.filing_status,
    )

    return TaxLiabilityOutput(**result)


# ─── Asset Location Endpoints ──────────────────────────────────────────────────

@router.post("/asset-location/recommendations", response_model=list[AssetLocationOutput])
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_asset_location_recommendations(
    request: Request,
    positions: list[AssetLocationRecommendationInput],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> list[AssetLocationOutput]:
    """
    Get asset location optimization recommendations.

    Identifies which assets should be moved between account types to minimize taxes.
    Tax-inefficient assets (bonds, REITs) should be in tax-deferred accounts.
    Tax-efficient assets (growth stocks, ETFs) can stay in taxable accounts.
    """
    service = AssetLocationService()

    pos_objects = [
        Position(
            symbol=p.symbol,
            asset_type=AssetType(p.asset_type),
            quantity=p.quantity,
            current_price=p.current_price,
            cost_basis=p.cost_basis,
            annual_distribution=p.annual_distribution,
            turnover_rate=p.turnover_rate,
        )
        for p in positions
    ]

    # Create synthetic account list
    accounts = []  # Could add actual account info here

    recommendations = service.get_recommendations(pos_objects, accounts)

    return [
        AssetLocationOutput(
            symbol=r.symbol,
            current_account=r.current_account.value,
            recommended_account=r.recommended_account.value,
            reason=r.reason,
            estimated_tax_savings=r.estimated_tax_savings,
            quantity=r.quantity,
            priority=r.priority,
        )
        for r in recommendations
    ]


# ─── Withdrawal Strategy Endpoints ───────────────────────────────────────────

@router.post("/withdrawal/strategy", response_model=WithdrawalPlanOutput)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_withdrawal_strategy(
    request: Request,
    strategy: WithdrawalStrategyInput,
    current_user: Annotated[dict, Depends(get_current_user)],
    start_year: int = 1,
) -> WithdrawalPlanOutput:
    """
    Generate tax-efficient retirement withdrawal strategy.

    Optimal sequence:
    1. Roth IRA (tax-free)
    2. Taxable account (capital gains treatment)
    3. Traditional IRA / 401k (ordinary income, RMDs)
    4. HSA (medical expenses first)

    Accounts for Social Security, RMDs, and tax bracket management.
    """
    service = TaxEfficientWithdrawalService(
        current_age=strategy.current_age,
        filing_status=strategy.filing_status,
    )

    plan = service.generate_withdrawal_sequence(
        annual_expenses=strategy.annual_expenses,
        start_year=start_year,
        years_to_plan=strategy.years_to_plan,
        social_security_annual=strategy.social_security_annual,
    )

    return WithdrawalPlanOutput(
        yearly_withdrawals=[
            YearlyWithdrawalOutput(
                year=y.year,
                age=y.age,
                total_withdrawn=y.total_withdrawn,
                total_tax=y.total_tax,
                effective_tax_rate=y.effective_tax_rate,
                marginal_tax_rate=y.marginal_tax_rate,
                rmd_required=y.rmd_required,
                steps=[
                    {
                        "step_number": s.step_number,
                        "source": s.source.value,
                        "amount": s.amount,
                        "tax_impact": s.tax_impact,
                        "rationale": s.rationale,
                        "cumulative_tax": s.cumulative_tax,
                    }
                    for s in y.withdrawal_steps
                ],
            )
            for y in plan.years
        ],
        total_withdrawn=plan.total_withdrawn,
        total_taxes_paid=plan.total_taxes_paid,
        effective_tax_rate=plan.effective_tax_rate,
        roth_percentage_at_end=plan.roth_percentage_at_end,
    )

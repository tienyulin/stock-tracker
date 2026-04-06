"""
Simulation endpoints for Monte Carlo retirement planning.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, model_validator

from app.core.rate_limiter import limiter, DEFAULT_RATE_LIMIT
from app.services.monte_carlo_service import MonteCarloService
from app.schemas.schemas import RetirementSimulationRequest as SchemaRequest
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/simulation", tags=["Simulation"])


class AllocationInput(BaseModel):
    """Portfolio allocation input."""
    stocks: float = Field(default=0.6, ge=0, le=1)
    bonds: float = Field(default=0.3, ge=0, le=1)
    cash: float = Field(default=0.05, ge=0, le=1)
    real_estate: float = Field(default=0.05, ge=0, le=1)


class RetirementSimulationRequest(BaseModel):
    """Request model for retirement simulation."""
    current_age: int = Field(default=30, ge=18, le=100)
    retirement_age: int = Field(default=65, ge=18, le=100)
    life_expectancy: int = Field(default=95, ge=18, le=120)
    current_portfolio: float = Field(default=100000, ge=0)
    monthly_contribution: float = Field(default=1000, ge=0)
    desired_monthly_income: float = Field(default=5000, ge=0)
    desired_annual_income: float = Field(default=60000, ge=0)
    social_security_monthly: float = Field(default=0, ge=0)
    num_simulations: int = Field(default=10000, ge=100, le=100000)
    portfolio_allocation: dict[str, float] = Field(
        default_factory=lambda: {"stocks": 0.6, "bonds": 0.3, "cash": 0.05, "real_estate": 0.05}
    )
    years_to_simulate: int = Field(default=10, ge=0)

    @model_validator(mode="after")
    def validate_ages(self):
        if self.retirement_age <= self.current_age:
            raise ValueError("retirement_age must be greater than current_age")
        if self.life_expectancy <= self.retirement_age:
            raise ValueError("life_expectancy must be greater than retirement_age")
        return self


class YearlyOutcome(BaseModel):
    """Year-by-year outcome."""
    year: int
    age: int
    median_balance: float
    is_retirement: bool


class RetirementSimulationResponse(BaseModel):
    """Response model for retirement simulation."""
    success_probability: float
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
    assumptions: dict


@router.post("/retirement", response_model=RetirementSimulationResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def run_retirement_simulation(
    request: Request,
    body: RetirementSimulationRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> RetirementSimulationResponse:
    """
    Run Monte Carlo simulation for retirement planning.
    
    Simulates multiple scenarios with stochastic market returns
    based on historical volatility and return assumptions.
    
    Returns success rate and percentile outcomes for retirement outcomes.
    """
    # Convert to schema request
    schema_req = SchemaRequest(
        current_age=body.current_age,
        retirement_age=body.retirement_age,
        life_expectancy=body.life_expectancy,
        current_savings=body.current_portfolio,
        monthly_contribution=body.monthly_contribution,
        desired_monthly_income=body.desired_monthly_income,
        social_security_monthly=body.social_security_monthly,
        num_simulations=body.num_simulations,
        portfolio_allocation=body.portfolio_allocation,
        years_to_simulate=body.years_to_simulate,
    )
    
    service = MonteCarloService()
    result = service.run_retirement_simulation(schema_req)
    
    return RetirementSimulationResponse(
        success_probability=result.success_probability,
        median_outcome=result.median_outcome,
        percentile_10=result.percentile_10,
        percentile_25=result.percentile_25,
        percentile_75=result.percentile_75,
        percentile_90=result.percentile_90,
        average_outcome=result.average_outcome,
        worst_outcome=result.worst_outcome,
        best_outcome=result.best_outcome,
        total_simulations=result.total_simulations,
        years_until_retirement=result.years_until_retirement,
        assumptions=result.assumptions,
    )

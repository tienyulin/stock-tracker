"""
Simulation endpoints for Monte Carlo retirement planning.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.core.rate_limiter import limiter, DEFAULT_RATE_LIMIT
from app.services.monte_carlo_service import (
    MonteCarloService,
    PortfolioAllocation,
    RetirementParams,
)
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
    retirement_age: int = Field(default=65, ge=current_age, le=100)
    life_expectancy: int = Field(default=95, ge=retirement_age, le=120)
    current_portfolio: float = Field(default=100000, ge=0)
    monthly_contribution: float = Field(default=1000, ge=0)
    desired_annual_income: float = Field(default=60000, ge=0)
    social_security_monthly: float = Field(default=0, ge=0)
    allocation: AllocationInput = Field(default_factory=AllocationInput)


class YearlyOutcome(BaseModel):
    """Year-by-year outcome."""
    year: int
    age: int
    median_balance: float
    is_retirement: bool


class RetirementSimulationResponse(BaseModel):
    """Response model for retirement simulation."""
    success_rate: float = Field(description="Percentage of simulations that didn't run out of money")
    median_ending_balance: float
    percentile_10: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    yearly_outcomes: list[YearlyOutcome]
    total_contributions: float
    total_growth: float
    simulation_count: int = Field(default=10000)


@router.post("/retirement", response_model=RetirementSimulationResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def run_retirement_simulation(
    request: Request,
    body: RetirementSimulationRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> RetirementSimulationResponse:
    """
    Run Monte Carlo simulation for retirement planning.
    
    Simulates 10,000 scenarios with stochastic market returns
    based on historical volatility and return assumptions.
    
    Returns success rate and percentile outcomes for retirement outcomes.
    """
    # Build allocation
    alloc = body.allocation
    portfolio_alloc = PortfolioAllocation(
        stocks=alloc.stocks,
        bonds=alloc.bonds,
        cash=alloc.cash,
        real_estate=alloc.real_estate
    )
    
    # Build params
    params = RetirementParams(
        current_age=body.current_age,
        retirement_age=body.retirement_age,
        life_expectancy=body.life_expectancy,
        current_portfolio=body.current_portfolio,
        monthly_contribution=body.monthly_contribution,
        desired_annual_income=body.desired_annual_income,
        social_security_monthly=body.social_security_monthly,
        allocation=portfolio_alloc
    )
    
    # Run simulation
    service = MonteCarloService()
    result = await service.simulate(params)
    
    return RetirementSimulationResponse(
        success_rate=result.success_rate,
        median_ending_balance=result.median_ending_balance,
        percentile_10=result.percentile_10,
        percentile_25=result.percentile_25,
        percentile_75=result.percentile_75,
        percentile_90=result.percentile_90,
        yearly_outcomes=[
            YearlyOutcome(**y) for y in result.yearly_outcomes
        ],
        total_contributions=result.total_contributions,
        total_growth=result.total_growth,
        simulation_count=10000
    )

"""
Stress Testing API endpoints.

Provides portfolio stress testing, scenario analysis, and sensitivity analysis.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.core.rate_limiter import limiter, DEFAULT_RATE_LIMIT
from app.services.stress_test_service import StressTestService
from app.schemas.stress_test_schemas import (
    StressTestRequest,
    StressTestResponse,
    SensitivityAnalysisRequest,
    SensitivityAnalysisResponse,
    ScenarioComparisonResponse,
    StressTestSummary,
)
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/stress-test", tags=["Stress Testing"])


def get_stress_test_service() -> StressTestService:
    """Dependency injection for StressTestService."""
    return StressTestService()


@router.post("/run", response_model=StressTestResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def run_stress_test(
    request: Request,
    body: StressTestRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[StressTestService, Depends(get_stress_test_service)],
) -> StressTestResponse:
    """
    Run a stress test scenario on the portfolio.

    Supports predefined scenarios (2008 crisis, COVID crash, etc.) or custom shocks.
    Returns VaR, CVaR, percentile distributions, and risk metrics.
    """
    return service.run_stress_test(body)


class CompareScenariosRequest(BaseModel):
    """Request model for scenario comparison."""
    portfolio_value: float = Field(..., gt=0)


@router.post("/compare", response_model=ScenarioComparisonResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def compare_stress_scenarios(
    request: Request,
    body: CompareScenariosRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[StressTestService, Depends(get_stress_test_service)],
) -> ScenarioComparisonResponse:
    """
    Compare all predefined stress test scenarios.

    Runs 2008 Financial Crisis, COVID-19 Crash, Great Depression,
    and Dot-Com Bubble scenarios against the portfolio.
    """
    return service.compare_scenarios(body.portfolio_value)


@router.post("/sensitivity", response_model=SensitivityAnalysisResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def run_sensitivity_analysis(
    request: Request,
    body: SensitivityAnalysisRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[StressTestService, Depends(get_stress_test_service)],
) -> SensitivityAnalysisResponse:
    """
    Run sensitivity analysis on portfolio holdings.

    Analyzes interest rate sensitivity, FX sensitivity, and correlation impact.
    Returns per-asset sensitivity ratings and recommendations.
    """
    return service.run_sensitivity_analysis(body)


class StressTestSummaryRequest(BaseModel):
    """Request model for stress test summary."""
    portfolio_value: float = Field(..., gt=0)
    portfolio_id: Optional[str] = None


@router.post("/summary", response_model=StressTestSummary)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_stress_test_summary(
    request: Request,
    body: StressTestSummaryRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    service: Annotated[StressTestService, Depends(get_stress_test_service)],
) -> StressTestSummary:
    """
    Get a summary of stress test results for a portfolio.

    Includes worst-case scenario, VaR metrics, and overall risk rating.
    """
    portfolio_value = body.portfolio_value
    portfolio_id = body.portfolio_id
    comparison = service.compare_scenarios(portfolio_value)
    worst = comparison.worst_case

    # Get VaR for 1-day and 1-year
    var_request = StressTestRequest(
        scenario_type=comparison.scenarios[0].scenario_type,
        portfolio_value=portfolio_value,
        holdings=[],
        num_simulations=10000,
    )
    var_response = service.run_stress_test(var_request)

    risk_rating = "low"
    if worst.loss_percent > 0.40:
        risk_rating = "very_high"
    elif worst.loss_percent > 0.25:
        risk_rating = "high"
    elif worst.loss_percent > 0.15:
        risk_rating = "moderate"

    return StressTestSummary(
        portfolio_id=portfolio_id,
        total_value=portfolio_value,
        worst_scenario_loss=abs(worst.loss_amount),
        worst_scenario_loss_percent=abs(worst.loss_percent),
        var_95_1day=var_response.var_result.var_95,
        var_99_1day=var_response.var_result.var_99,
        diversification_score=comparison.portfolio_diversification_score,
        risk_rating=risk_rating,
        scenarios_tested=len(comparison.scenarios),
        timestamp=var_response.timestamp,
    )

"""
Stress Testing Schemas

Pydantic models for portfolio stress testing and scenario analysis.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ScenarioType(str, Enum):
    """Predefined stress test scenario types."""

    FINANCIAL_CRISIS_2008 = "financial_crisis_2008"
    COVID_CRASH_2020 = "covid_crash_2020"
    GREAT_DEPRESSION_1929 = "great_depression_1929"
    DOT_COM_BUBBLE_2000 = "dot_com_bubble_2000"
    CUSTOM = "custom"


class AssetClass(str, Enum):
    """Asset class types for scenario analysis."""

    STOCKS = "stocks"
    BONDS = "bonds"
    CASH = "cash"
    REAL_ESTATE = "real_estate"
    COMMODITIES = "commodities"
    OPTIONS = "options"


class StressTestRequest(BaseModel):
    """Request model for stress test simulation."""

    scenario_type: ScenarioType = Field(..., description="Predefined or custom scenario")
    portfolio_value: float = Field(..., ge=0, description="Total portfolio value")
    holdings: list[dict] = Field(
        default_factory=list,
        description="List of holdings with ticker, shares, cost_basis",
    )
    custom_shock: Optional[dict[str, float]] = Field(
        None,
        description="Custom shock percentages per asset class (e.g., {'stocks': -0.30})",
    )
    confidence_level: float = Field(default=0.95, ge=0.9, le=0.99)
    num_simulations: int = Field(default=10000, ge=1000, le=100000)


class CustomScenarioRequest(BaseModel):
    """Request model for custom stress scenario."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    market_decline_percent: float = Field(..., ge=-1, le=1, description="Overall market decline")
    bond_rate_change: float = Field(default=0.0, ge=-0.5, le=0.5, description="Interest rate change")
    currency_devaluation: float = Field(
        default=0.0, ge=-0.5, le=0.5, description="Currency devaluation vs USD"
    )
    correlation_multiplier: float = Field(
        default=1.0, ge=0.0, le=3.0, description="Asset correlation multiplier"
    )


class ScenarioResult(BaseModel):
    """Result of a single scenario simulation."""

    scenario_name: str
    scenario_type: ScenarioType
    initial_value: float
    stressed_value: float
    loss_amount: float
    loss_percent: float
    recovery_years: Optional[int] = None


class PercentileResult(BaseModel):
    """Percentile distribution result."""

    percentile_5: float
    percentile_25: float
    percentile_50: float
    percentile_75: float
    percentile_95: float


class VarResult(BaseModel):
    """Value at Risk result."""

    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    confidence_level: float


class RiskMetricResult(BaseModel):
    """Individual risk metric result."""

    metric_name: str
    value: float
    threshold: Optional[float] = None
    breached: bool = False


class SensitivityResult(BaseModel):
    """Sensitivity analysis result for an asset."""

    asset_ticker: str
    contribution_to_portfolio: float
    impact_on_portfolio: float
    sensitivity_rating: str = Field(
        ..., pattern="^(low|medium|high|critical)$"
    )


class StressTestResponse(BaseModel):
    """Response model for stress test results."""

    scenario_name: str
    scenario_type: ScenarioType
    initial_value: float
    stressed_value: float
    loss_amount: float
    loss_percent: float
    var_result: VarResult
    percentiles: PercentileResult
    risk_metrics: list[RiskMetricResult]
    confidence_level: float
    timestamp: str


class ScenarioComparisonResponse(BaseModel):
    """Comparison of multiple stress test scenarios."""

    scenarios: list[ScenarioResult]
    worst_case: ScenarioResult
    best_case: ScenarioResult
    portfolio_diversification_score: float
    recommendation: str


class SensitivityAnalysisRequest(BaseModel):
    """Request model for sensitivity analysis."""

    holdings: list[dict] = Field(..., description="Portfolio holdings")
    analysis_type: str = Field(
        default="full", pattern="^(full|interest_rate|fx|correlation)$"
    )
    interest_rate_shift: float = Field(default=0.01, ge=-0.05, le=0.05)
    fx_shock: float = Field(default=0.1, ge=-0.5, le=0.5)


class SensitivityAnalysisResponse(BaseModel):
    """Response model for sensitivity analysis."""

    analysis_type: str
    base_portfolio_value: float
    stressed_value: float
    impact: float
    impact_percent: float
    asset_sensitivities: list[SensitivityResult]
    recommendations: list[str]


class StressTestSummary(BaseModel):
    """Summary of all stress test scenarios for a portfolio."""

    portfolio_id: Optional[UUID] = None
    total_value: float
    worst_scenario_loss: float
    worst_scenario_loss_percent: float
    var_95_1day: float
    var_99_1day: float
    diversification_score: float
    risk_rating: str = Field(..., pattern="^(low|moderate|high|very_high)$")
    scenarios_tested: int
    timestamp: str

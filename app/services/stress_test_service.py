"""
Stress Testing Service

Provides portfolio stress testing, scenario analysis, and risk metrics
including VaR, CVaR, and sensitivity analysis.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np

from app.schemas.stress_test_schemas import (
    ScenarioType,
    StressTestRequest,
    StressTestResponse,
    ScenarioResult,
    VarResult,
    PercentileResult,
    RiskMetricResult,
    SensitivityAnalysisRequest,
    SensitivityAnalysisResponse,
    SensitivityResult,
    ScenarioComparisonResponse,
    CustomScenarioRequest,
    StressTestSummary,
)


# Historical scenario parameters (annualized returns during crisis periods)
SCENARIO_PARAMS = {
    ScenarioType.FINANCIAL_CRISIS_2008: {
        "name": "2008 Financial Crisis",
        "stocks": -0.37,
        "bonds": 0.05,
        "cash": 0.02,
        "real_estate": -0.40,
        "commodities": -0.35,
        "description": "Lehman Brothers collapse, S&P 500 -37% in 2008",
    },
    ScenarioType.COVID_CRASH_2020: {
        "name": "COVID-19 Crash (2020)",
        "stocks": -0.34,
        "bonds": 0.08,
        "cash": 0.01,
        "real_estate": -0.25,
        "commodities": -0.20,
        "description": "COVID-19 pandemic, fastest bear market in history",
    },
    ScenarioType.GREAT_DEPRESSION_1929: {
        "name": "Great Depression (1929-1932)",
        "stocks": -0.48,
        "bonds": 0.06,
        "cash": 0.02,
        "real_estate": -0.35,
        "commodities": -0.40,
        "description": "Worst market decline in US history, Dow -89% peak to trough",
    },
    ScenarioType.DOT_COM_BUBBLE_2000: {
        "name": "Dot-Com Bubble (2000-2002)",
        "stocks": -0.40,
        "bonds": 0.08,
        "cash": 0.03,
        "real_estate": -0.10,
        "commodities": -0.15,
        "description": "Tech bubble burst, Nasdaq -78%",
    },
}

# Long-term average returns and volatility for Monte Carlo
MARKET_PARAMS = {
    "stocks": {"mean": 0.10, "std": 0.18},
    "bonds": {"mean": 0.05, "std": 0.06},
    "cash": {"mean": 0.02, "std": 0.01},
    "real_estate": {"mean": 0.08, "std": 0.12},
    "commodities": {"mean": 0.06, "std": 0.20},
}


@dataclass
class Holding:
    """Represents a portfolio holding."""

    ticker: str
    shares: float
    cost_basis: float
    current_price: float
    asset_class: str = "stocks"


class StressTestService:
    """Service for portfolio stress testing and scenario analysis."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize stress test service.

        Args:
            seed: Random seed for reproducibility in simulations.
        """
        self._rng = np.random.default_rng(seed)

    def run_stress_test(self, request: StressTestRequest) -> StressTestResponse:
        """Run a stress test scenario on the portfolio.

        Args:
            request: Stress test request with scenario and portfolio details.

        Returns:
            StressTestResponse with VaR, percentiles, and risk metrics.
        """
        if request.scenario_type == ScenarioType.CUSTOM:
            shock = request.custom_shock or {}
            scenario_name = "Custom Scenario"
            scenario_returns = shock
        else:
            params = SCENARIO_PARAMS.get(request.scenario_type, {})
            scenario_name = params.get("name", "Unknown")
            scenario_returns = {
                "stocks": params.get("stocks", -0.30),
                "bonds": params.get("bonds", 0.00),
                "cash": params.get("cash", 0.00),
                "real_estate": params.get("real_estate", -0.30),
                "commodities": params.get("commodities", -0.30),
            }

        stressed_value = self._calculate_stressed_value(
            request.portfolio_value, scenario_returns, request.holdings
        )
        loss_amount = request.portfolio_value - stressed_value
        loss_percent = loss_amount / request.portfolio_value if request.portfolio_value > 0 else 0

        # Run Monte Carlo for VaR
        var_result = self._calculate_var_monte_carlo(
            request.portfolio_value,
            request.num_simulations,
            request.confidence_level,
        )

        percentiles = self._calculate_percentiles(
            request.portfolio_value, loss_percent, request.num_simulations
        )

        risk_metrics = self._calculate_risk_metrics(
            request.portfolio_value, stressed_value, loss_percent
        )

        return StressTestResponse(
            scenario_name=scenario_name,
            scenario_type=request.scenario_type,
            initial_value=request.portfolio_value,
            stressed_value=stressed_value,
            loss_amount=loss_amount,
            loss_percent=loss_percent,
            var_result=var_result,
            percentiles=percentiles,
            risk_metrics=risk_metrics,
            confidence_level=request.confidence_level,
            timestamp=datetime.utcnow().isoformat(),
        )

    def _calculate_stressed_value(
        self,
        portfolio_value: float,
        scenario_returns: dict[str, float],
        holdings: list[dict],
    ) -> float:
        """Calculate stressed portfolio value based on scenario."""
        if not holdings:
            # Default: assume 70% stocks, 20% bonds, 10% cash
            stocks_weight = 0.70
            bonds_weight = 0.20
            cash_weight = 0.10
            stressed = (
                portfolio_value * stocks_weight * (1 + scenario_returns.get("stocks", -0.30))
                + portfolio_value * bonds_weight * (1 + scenario_returns.get("bonds", 0.00))
                + portfolio_value * cash_weight * (1 + scenario_returns.get("cash", 0.00))
            )
            return stressed

        # Calculate based on actual holdings
        total_value = 0.0
        for holding in holdings:
            ticker = holding.get("ticker", "UNKNOWN")
            shares = holding.get("shares", 0)
            current_price = holding.get("current_price", 0)
            value = shares * current_price

            # Determine asset class from ticker
            asset_class = self._classify_asset(ticker)
            shock = scenario_returns.get(asset_class, -0.20)
            stressed_value = value * (1 + shock)
            total_value += stressed_value

        return total_value if total_value > 0 else portfolio_value * 0.7

    def _classify_asset(self, ticker: str) -> str:
        """Classify ticker into asset class (simplified)."""
        ticker_upper = ticker.upper()
        bond_tickers = {"TLT", "BND", "AGG", "VCIT", "VCSH", "IEF", "LQD", "HYG"}
        cash_tickers = {"SHV", "BIL", "SHY", "IEF", "GSH"}
        reit_tickers = {"VNQ", "IYR", "SCHH", "O", "SPG", "AMT", "EQIX"}
        commodity_tickers = {"GLD", "SLV", "USO", "DBA", "PDBC", "DBCC"}

        if ticker_upper in bond_tickers:
            return "bonds"
        elif ticker_upper in cash_tickers:
            return "cash"
        elif ticker_upper in reit_tickers:
            return "real_estate"
        elif ticker_upper in commodity_tickers:
            return "commodities"
        return "stocks"

    def _calculate_var_monte_carlo(
        self,
        portfolio_value: float,
        num_simulations: int,
        confidence_level: float,
    ) -> VarResult:
        """Calculate VaR using Monte Carlo simulation."""
        # Daily returns assumption (annualized 10%, std 18%)
        daily_mean = 0.10 / 252
        daily_std = 0.18 / math.sqrt(252)

        # Simulate daily returns
        returns = self._rng.normal(daily_mean, daily_std, num_simulations)
        portfolio_returns = returns * portfolio_value

        # Sort for VaR calculation
        sorted_returns = np.sort(portfolio_returns)
        var_95_idx = int(num_simulations * (1 - 0.95))
        var_99_idx = int(num_simulations * (1 - 0.99))

        var_95 = abs(sorted_returns[var_95_idx])
        var_99 = abs(sorted_returns[var_99_idx])

        # CVaR (Expected Shortfall)
        cvar_95 = abs(np.mean(sorted_returns[:var_95_idx]))
        cvar_99 = abs(np.mean(sorted_returns[:var_99_idx]))

        return VarResult(
            var_95=round(var_95, 2),
            var_99=round(var_99, 2),
            cvar_95=round(cvar_95, 2),
            cvar_99=round(cvar_99, 2),
            confidence_level=confidence_level,
        )

    def _calculate_percentiles(
        self,
        portfolio_value: float,
        loss_percent: float,
        num_simulations: int,
    ) -> PercentileResult:
        """Calculate percentile distribution of portfolio outcomes."""
        # Use Monte Carlo to simulate distribution
        daily_mean = 0.10 / 252
        daily_std = 0.18 / math.sqrt(252)

        # Simulate 1-year outcomes
        yearly_returns = self._rng.normal(daily_mean * 252, daily_std * math.sqrt(252), num_simulations)
        portfolio_values = portfolio_value * (1 + yearly_returns)

        return PercentileResult(
            percentile_5=round(np.percentile(portfolio_values, 5), 2),
            percentile_25=round(np.percentile(portfolio_values, 25), 2),
            percentile_50=round(np.percentile(portfolio_values, 50), 2),
            percentile_75=round(np.percentile(portfolio_values, 75), 2),
            percentile_95=round(np.percentile(portfolio_values, 95), 2),
        )

    def _calculate_risk_metrics(
        self,
        portfolio_value: float,
        stressed_value: float,
        loss_percent: float,
    ) -> list[RiskMetricResult]:
        """Calculate various risk metrics."""
        metrics = []

        # Maximum Drawdown
        max_drawdown = abs(loss_percent)
        metrics.append(RiskMetricResult(
            metric_name="Maximum Drawdown",
            value=round(max_drawdown, 4),
            threshold=0.20,
            breached=max_drawdown > 0.20,
        ))

        # Volatility
        daily_std = 0.18 / math.sqrt(252)
        annualized_vol = daily_std * math.sqrt(252)
        metrics.append(RiskMetricResult(
            metric_name="Annualized Volatility",
            value=round(annualized_vol, 4),
            threshold=0.25,
            breached=annualized_vol > 0.25,
        ))

        # Sharpe Ratio (simplified)
        risk_free = 0.04
        expected_return = 0.10
        sharpe = (expected_return - risk_free) / 0.18
        metrics.append(RiskMetricResult(
            metric_name="Sharpe Ratio",
            value=round(sharpe, 3),
            threshold=1.0,
            breached=sharpe < 1.0,
        ))

        # Sortino Ratio
        downside_std = 0.12  # Approximate downside deviation
        sortino = (expected_return - risk_free) / downside_std
        metrics.append(RiskMetricResult(
            metric_name="Sortino Ratio",
            value=round(sortino, 3),
            threshold=1.0,
            breached=sortino < 1.0,
        ))

        # Loss vs Portfolio Value
        metrics.append(RiskMetricResult(
            metric_name="Stressed Loss Amount",
            value=round(portfolio_value - stressed_value, 2),
            threshold=portfolio_value * 0.20,
            breached=(portfolio_value - stressed_value) > portfolio_value * 0.20,
        ))

        return metrics

    def run_sensitivity_analysis(
        self, request: SensitivityAnalysisRequest
    ) -> SensitivityAnalysisResponse:
        """Run sensitivity analysis on portfolio holdings.

        Args:
            request: Sensitivity analysis request with holdings.

        Returns:
            SensitivityAnalysisResponse with per-asset sensitivities.
        """
        total_value = sum(
            h.get("shares", 0) * h.get("current_price", 0)
            for h in request.holdings
        )

        base_value = total_value
        stressed_value = base_value
        asset_sensitivities = []

        for holding in request.holdings:
            ticker = holding.get("ticker", "UNKNOWN")
            shares = holding.get("shares", 0)
            current_price = holding.get("current_price", 0)
            value = shares * current_price
            weight = value / base_value if base_value > 0 else 0

            asset_class = self._classify_asset(ticker)
            impact = 0.0

            if request.analysis_type in ("full", "interest_rate"):
                # Interest rate sensitivity
                if asset_class == "bonds":
                    # Duration approximation: price change ≈ -duration × rate_change
                    duration = 7.0  # Approximate bond duration
                    rate_change = request.interest_rate_shift
                    impact = -duration * rate_change * weight
                elif asset_class == "real_estate":
                    impact = -2.0 * request.interest_rate_shift * weight

            if request.analysis_type in ("full", "fx"):
                # FX sensitivity (simplified)
                if not any(c in ticker.upper() for c in ["USD", "US"]):
                    impact += request.fx_shock * weight

            impact_on_portfolio = base_value * impact
            stressed_value += impact_on_portfolio

            sensitivity_rating = "low"
            if abs(impact) > 0.15:
                sensitivity_rating = "critical"
            elif abs(impact) > 0.05:
                sensitivity_rating = "high"
            elif abs(impact) > 0.02:
                sensitivity_rating = "medium"

            asset_sensitivities.append(SensitivityResult(
                asset_ticker=ticker,
                contribution_to_portfolio=round(weight, 4),
                impact_on_portfolio=round(impact_on_portfolio, 2),
                sensitivity_rating=sensitivity_rating,
            ))

        total_impact = stressed_value - base_value
        total_impact_pct = total_impact / base_value if base_value > 0 else 0

        recommendations = []
        if total_impact_pct < -0.10:
            recommendations.append("Consider reducing interest rate sensitive assets")
        if total_impact_pct < -0.05:
            recommendations.append("Diversify currency exposure to reduce FX risk")
        critical_assets = [s for s in asset_sensitivities if s.sensitivity_rating == "critical"]
        if critical_assets:
            recommendations.append(
                f"Review allocation to high-sensitivity assets: {', '.join(s.asset_ticker for s in critical_assets)}"
            )

        return SensitivityAnalysisResponse(
            analysis_type=request.analysis_type,
            base_portfolio_value=round(base_value, 2),
            stressed_value=round(stressed_value, 2),
            impact=round(total_impact, 2),
            impact_percent=round(total_impact_pct, 4),
            asset_sensitivities=asset_sensitivities,
            recommendations=recommendations,
        )

    def compare_scenarios(self, portfolio_value: float) -> ScenarioComparisonResponse:
        """Compare all predefined stress test scenarios.

        Args:
            portfolio_value: Current portfolio value.

        Returns:
            ScenarioComparisonResponse with scenario results.
        """
        results = []

        for scenario_type in [
            ScenarioType.FINANCIAL_CRISIS_2008,
            ScenarioType.COVID_CRASH_2020,
            ScenarioType.GREAT_DEPRESSION_1929,
            ScenarioType.DOT_COM_BUBBLE_2000,
        ]:
            request = StressTestRequest(
                scenario_type=scenario_type,
                portfolio_value=portfolio_value,
                holdings=[],
            )
            response = self.run_stress_test(request)
            results.append(ScenarioResult(
                scenario_name=response.scenario_name,
                scenario_type=response.scenario_type,
                initial_value=response.initial_value,
                stressed_value=response.stressed_value,
                loss_amount=response.loss_amount,
                loss_percent=response.loss_percent,
            ))

        worst_case = max(results, key=lambda x: x.loss_percent)  # highest loss = worst
        best_case = min(results, key=lambda x: x.loss_percent)  # lowest loss = best

        # Calculate diversification score
        loss_pcts = [r.loss_percent for r in results]
        std_dev = np.std(loss_pcts)
        diversification_score = round(min(std_dev * 10, 1.0), 3)

        recommendation = "Portfolio shows "
        if diversification_score > 0.7:
            recommendation += "strong diversification across asset classes."
        elif diversification_score > 0.4:
            recommendation += "moderate diversification. Consider adding bonds or alternatives."
        else:
            recommendation += "poor diversification. High correlation across holdings increases stress scenario risk."

        return ScenarioComparisonResponse(
            scenarios=results,
            worst_case=worst_case,
            best_case=best_case,
            portfolio_diversification_score=diversification_score,
            recommendation=recommendation,
        )


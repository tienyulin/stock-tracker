"""
Monte Carlo Retirement Simulation Service

Runs Monte Carlo simulations for retirement planning.
"""

import math
import random
from dataclasses import dataclass

import numpy as np

from app.schemas.schemas import (
    RetirementSimulationRequest,
    RetirementSimulationResponse,
)


# Historical market assumptions (annual returns and volatility by asset class)
MARKET_ASSUMPTIONS = {
    "stocks": {"mean": 0.10, "std": 0.18},  # S&P 500 historical
    "bonds": {"mean": 0.05, "std": 0.06},  # Bond index historical
    "cash": {"mean": 0.02, "std": 0.01},  # Money market / T-bills
    "real_estate": {"mean": 0.08, "std": 0.12},  # REITs historical
}


@dataclass
class SimulationResult:
    """Result of a single Monte Carlo simulation path."""

    final_value: float
    yearly_values: list[float]


class MonteCarloService:
    """Service for Monte Carlo retirement simulations."""

    def __init__(self, seed: int | None = None):
        """Initialize Monte Carlo Service.

        Args:
            seed: Random seed for reproducibility in testing.
        """
        if seed is not None:
            self._rng = random.Random(seed)
            np.random.seed(seed)
        else:
            self._rng = random.Random()

    def run_retirement_simulation(
        self, request: RetirementSimulationRequest
    ) -> RetirementSimulationResponse:
        """Run Monte Carlo simulation for retirement planning.

        Args:
            request: Simulation parameters.

        Returns:
            Simulation results with probability distribution.
        """
        years_to_retirement = request.retirement_age - request.current_age
        if years_to_retirement <= 0:
            raise ValueError("Retirement age must be greater than current age.")

        years = years_to_retirement + (request.years_to_simulate or 10)
        num_sims = request.num_simulations

        # Calculate blended portfolio return parameters
        portfolio_mean, portfolio_std = self._blended_portfolio_params(
            request.portfolio_allocation
        )

        # Run simulations
        outcomes: list[float] = []
        for _ in range(num_sims):
            final_value = self._single_simulation(
                current_savings=request.current_savings,
                monthly_contribution=request.monthly_contribution,
                years=years,
                mean=portfolio_mean,
                std=portfolio_std,
            )
            outcomes.append(final_value)

        outcomes.sort()

        # Calculate statistics
        percentile_10_idx = int(num_sims * 0.10)
        percentile_25_idx = int(num_sims * 0.25)
        percentile_75_idx = int(num_sims * 0.75)
        percentile_90_idx = int(num_sims * 0.90)

        median_outcome = outcomes[num_sims // 2]
        avg_outcome = sum(outcomes) / num_sims

        # Success = can withdraw desired monthly income for 30 years
        withdrawal_rate = (request.desired_monthly_income * 12) / median_outcome if median_outcome > 0 else 0
        safe_withdrawal_rate = 0.04  # 4% rule
        success_count = sum(
            1 for v in outcomes if v > 0 and (v * safe_withdrawal_rate) >= request.desired_monthly_income * 12
        )
        success_probability = success_count / num_sims

        return RetirementSimulationResponse(
            success_probability=round(success_probability, 4),
            median_outcome=round(median_outcome, 2),
            percentile_10=round(outcomes[percentile_10_idx], 2),
            percentile_25=round(outcomes[percentile_25_idx], 2),
            percentile_75=round(outcomes[percentile_75_idx], 2),
            percentile_90=round(outcomes[percentile_90_idx], 2),
            average_outcome=round(avg_outcome, 2),
            worst_outcome=round(min(outcomes), 2),
            best_outcome=round(max(outcomes), 2),
            total_simulations=num_sims,
            years_until_retirement=years_to_retirement,
            assumptions={
                "portfolio_mean": round(portfolio_mean, 4),
                "portfolio_std": round(portfolio_std, 4),
                "inflation_rate": 0.03,
                "withdrawal_years": 30,
            },
        )

    def _blended_portfolio_params(self, allocation: dict[str, float]) -> tuple[float, float]:
        """Calculate blended portfolio mean and std from allocation.

        Args:
            allocation: Dict of asset class -> weight.

        Returns:
            Tuple of (blended_mean, blended_std).
        """
        total_weight = sum(allocation.values())
        if not math.isclose(total_weight, 1.0, rel_tol=1e-5):
            raise ValueError(f"Portfolio allocation must sum to 1.0, got {total_weight}")

        blended_mean = 0.0
        blended_var = 0.0

        for asset, weight in allocation.items():
            if asset not in MARKET_ASSUMPTIONS:
                raise ValueError(f"Unknown asset class: {asset}")
            params = MARKET_ASSUMPTIONS[asset]
            blended_mean += weight * params["mean"]
            blended_var += (weight * params["std"]) ** 2

        blended_std = math.sqrt(blended_var)
        return blended_mean, blended_std

    def _single_simulation(
        self,
        current_savings: float,
        monthly_contribution: float,
        years: int,
        mean: float,
        std: float,
    ) -> float:
        """Run a single Monte Carlo simulation path.

        Uses geometric Brownian motion with monthly steps.

        Args:
            current_savings: Starting portfolio value.
            monthly_contribution: Monthly contribution amount.
            years: Number of years to simulate.
            mean: Annual mean return.
            std: Annual volatility.

        Returns:
            Final portfolio value.
        """
        monthly_mean = mean / 12
        monthly_std = std / math.sqrt(12)

        portfolio = current_savings

        for _ in range(years * 12):
            # Random monthly return using normal distribution
            monthly_return = np.random.normal(monthly_mean, monthly_std)
            portfolio = portfolio * (1 + monthly_return) + monthly_contribution

        return max(portfolio, 0)  # Can't go below 0

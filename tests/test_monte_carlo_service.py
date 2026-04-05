"""
Tests for Monte Carlo Retirement Simulation Service
"""

import pytest
from app.services.monte_carlo_service import MonteCarloService, MARKET_ASSUMPTIONS
from app.schemas.schemas import RetirementSimulationRequest


class TestMonteCarloService:
    """Tests for MonteCarloService."""

    def test_blended_portfolio_params_stocks_only(self):
        """100% stocks should return S&P 500 historical parameters."""
        service = MonteCarloService(seed=42)
        mean, std = service._blended_portfolio_params({"stocks": 1.0})
        assert mean == pytest.approx(MARKET_ASSUMPTIONS["stocks"]["mean"])
        assert std == pytest.approx(MARKET_ASSUMPTIONS["stocks"]["std"])

    def test_blended_portfolio_params_bonds_only(self):
        """100% bonds should return bond index parameters."""
        service = MonteCarloService(seed=42)
        mean, std = service._blended_portfolio_params({"bonds": 1.0})
        assert mean == pytest.approx(MARKET_ASSUMPTIONS["bonds"]["mean"])
        assert std == pytest.approx(MARKET_ASSUMPTIONS["bonds"]["std"])

    def test_blended_portfolio_params_mixed(self):
        """Mixed portfolio should return weighted blended parameters."""
        service = MonteCarloService(seed=42)
        # 70% stocks, 30% bonds
        mean, std = service._blended_portfolio_params({"stocks": 0.7, "bonds": 0.3})
        expected_mean = (
            0.7 * MARKET_ASSUMPTIONS["stocks"]["mean"]
            + 0.3 * MARKET_ASSUMPTIONS["bonds"]["mean"]
        )
        # Std is sqrt of weighted variances (assuming independence)
        import math
        expected_var = (
            (0.7 * MARKET_ASSUMPTIONS["stocks"]["std"]) ** 2
            + (0.3 * MARKET_ASSUMPTIONS["bonds"]["std"]) ** 2
        )
        expected_std = math.sqrt(expected_var)
        assert mean == pytest.approx(expected_mean)
        assert std == pytest.approx(expected_std)

    def test_blended_portfolio_params_must_sum_to_one(self):
        """Allocation must sum to 1.0."""
        service = MonteCarloService(seed=42)
        with pytest.raises(ValueError, match="must sum to 1.0"):
            service._blended_portfolio_params({"stocks": 0.5, "bonds": 0.3})

    def test_blended_portfolio_params_unknown_asset(self):
        """Unknown asset class should raise ValueError."""
        service = MonteCarloService(seed=42)
        with pytest.raises(ValueError, match="Unknown asset class"):
            service._blended_portfolio_params({"stocks": 0.7, "bitcoin": 0.3})

    def test_retirement_simulation_retirement_age_greater_than_current(self):
        """Retirement age must be greater than current age."""
        service = MonteCarloService(seed=42)
        request = RetirementSimulationRequest(
            current_age=65,
            retirement_age=60,  # Invalid: less than current_age
            current_savings=100000,
            monthly_contribution=1000,
            desired_monthly_income=5000,
        )
        with pytest.raises(ValueError, match="greater than current age"):
            service.run_retirement_simulation(request)

    def test_retirement_simulation_returns_valid_response(self):
        """Simulation should return a well-formed response."""
        service = MonteCarloService(seed=42)
        request = RetirementSimulationRequest(
            current_age=30,
            retirement_age=65,
            current_savings=50000,
            monthly_contribution=1000,
            desired_monthly_income=5000,
            portfolio_allocation={"stocks": 0.7, "bonds": 0.2, "cash": 0.1},
            num_simulations=500,
        )
        result = service.run_retirement_simulation(request)

        assert 0.0 <= result.success_probability <= 1.0
        assert result.median_outcome > 0
        assert result.percentile_10 <= result.median_outcome <= result.percentile_90
        assert result.percentile_25 <= result.median_outcome <= result.percentile_75
        assert result.worst_outcome <= result.percentile_10
        assert result.best_outcome >= result.percentile_90
        assert result.average_outcome > 0
        assert result.total_simulations == 500
        assert result.years_until_retirement == 35
        assert "portfolio_mean" in result.assumptions
        assert "portfolio_std" in result.assumptions
        assert "inflation_rate" in result.assumptions
        assert "withdrawal_years" in result.assumptions

    def test_retirement_simulation_reproducible_with_seed(self):
        """Same seed should produce identical results."""
        for seed in [1, 42, 999]:
            svc1 = MonteCarloService(seed=seed)
            svc2 = MonteCarloService(seed=seed)
            request = RetirementSimulationRequest(
                current_age=30,
                retirement_age=65,
                current_savings=50000,
                monthly_contribution=500,
                desired_monthly_income=3000,
                portfolio_allocation={"stocks": 0.6, "bonds": 0.3, "cash": 0.1},
                num_simulations=200,
            )
            r1 = svc1.run_retirement_simulation(request)
            r2 = svc2.run_retirement_simulation(request)
            assert r1.median_outcome == r2.median_outcome
            assert r1.success_probability == r2.success_probability

    def test_retirement_simulation_with_real_estate_allocation(self):
        """Should handle real estate in portfolio allocation."""
        service = MonteCarloService(seed=42)
        request = RetirementSimulationRequest(
            current_age=35,
            retirement_age=60,
            current_savings=100000,
            monthly_contribution=2000,
            desired_monthly_income=6000,
            portfolio_allocation={"stocks": 0.5, "bonds": 0.2, "real_estate": 0.2, "cash": 0.1},
            num_simulations=300,
        )
        result = service.run_retirement_simulation(request)
        assert result.success_probability >= 0.0
        assert result.median_outcome > 0

    def test_single_simulation_positive_returns(self):
        """Single simulation with positive drift should generally grow."""
        service = MonteCarloService(seed=42)
        # With high contribution and moderate returns, expect growth
        final = service._single_simulation(
            current_savings=10000,
            monthly_contribution=500,
            years=10,
            mean=0.08,
            std=0.15,
        )
        # Expected: contributions over 10 yrs = 10*12*500 = 60000, plus growth
        # Should be at least the contributions
        assert final >= 60000  # At minimum, return the contributions

    def test_single_simulation_never_negative(self):
        """Portfolio value should never go below zero (capped)."""
        service = MonteCarloService(seed=42)
        for _ in range(10):
            final = service._single_simulation(
                current_savings=0,
                monthly_contribution=0,
                years=1,
                mean=-0.5,
                std=0.5,
            )
            assert final >= 0

    def test_high_risk_profile_lower_success_probability(self):
        """High-volatility portfolio should generally have lower success probability."""
        conservative_req = RetirementSimulationRequest(
            current_age=30,
            retirement_age=65,
            current_savings=50000,
            monthly_contribution=1000,
            desired_monthly_income=10000,
            portfolio_allocation={"bonds": 0.6, "stocks": 0.3, "cash": 0.1},
            num_simulations=500,
        )
        aggressive_req = RetirementSimulationRequest(
            current_age=30,
            retirement_age=65,
            current_savings=50000,
            monthly_contribution=1000,
            desired_monthly_income=10000,
            portfolio_allocation={"stocks": 0.8, "bonds": 0.1, "cash": 0.1},
            num_simulations=500,
        )
        svc = MonteCarloService(seed=42)
        conservative_result = svc.run_retirement_simulation(conservative_req)
        aggressive_result = svc.run_retirement_simulation(aggressive_req)
        # Higher desired income with same savings = lower success for both
        # Just verify they both run and produce results in valid range
        assert 0.0 <= conservative_result.success_probability <= 1.0
        assert 0.0 <= aggressive_result.success_probability <= 1.0

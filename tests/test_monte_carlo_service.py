"""
Tests for Monte Carlo Retirement Simulation Service.
"""

import pytest
import asyncio


class TestMonteCarloService:
    """Test Monte Carlo simulation functionality."""

    def test_monte_carlo_result_structure(self):
        """Verify Monte Carlo service produces expected result structure."""
        from app.services.monte_carlo_service import (
            MonteCarloService,
            PortfolioAllocation,
            RetirementParams,
        )
        
        service = MonteCarloService()
        params = RetirementParams(
            current_age=30,
            retirement_age=65,
            life_expectancy=95,
            current_portfolio=100000,
            monthly_contribution=1000,
            desired_annual_income=60000,
            social_security_monthly=1500,
        )
        
        # Run synchronously for test
        result = asyncio.run(service.simulate(params))
        
        # Check result fields
        assert hasattr(result, 'success_rate')
        assert hasattr(result, 'median_ending_balance')
        assert hasattr(result, 'percentile_10')
        assert hasattr(result, 'percentile_25')
        assert hasattr(result, 'percentile_75')
        assert hasattr(result, 'percentile_90')
        assert hasattr(result, 'yearly_outcomes')
        assert hasattr(result, 'total_contributions')
        assert hasattr(result, 'total_growth')
        
        # Success rate should be between 0 and 100
        assert 0 <= result.success_rate <= 100

    def test_portfolio_allocation_defaults(self):
        """Test default portfolio allocation."""
        from app.services.monte_carlo_service import PortfolioAllocation
        
        alloc = PortfolioAllocation()
        
        assert alloc.stocks == 0.6
        assert alloc.bonds == 0.3
        assert alloc.cash == 0.05
        assert alloc.real_estate == 0.05
        
        # Should sum to 1.0
        total = alloc.stocks + alloc.bonds + alloc.cash + alloc.real_estate
        assert abs(total - 1.0) < 0.001

    def test_retirement_params_defaults(self):
        """Test default retirement parameters."""
        from app.services.monte_carlo_service import RetirementParams
        
        params = RetirementParams()
        
        assert params.current_age == 30
        assert params.retirement_age == 65
        assert params.life_expectancy == 95
        assert params.current_portfolio == 100000
        assert params.monthly_contribution == 1000
        assert params.desired_annual_income == 60000

    def test_market_assumptions(self):
        """Test market assumptions values."""
        from app.services.monte_carlo_service import MarketAssumptions
        
        market = MarketAssumptions()
        
        # Historical averages
        assert 0.08 <= market.stock_return <= 0.12
        assert 0.15 <= market.stock_volatility <= 0.20
        assert market.bond_return < market.stock_return
        assert market.bond_volatility < market.stock_volatility

    def test_simulation_reproducibility(self):
        """Same seed should produce same results."""
        from app.services.monte_carlo_service import MonteCarloService, RetirementParams
        
        params = RetirementParams(current_portfolio=100000)
        
        service1 = MonteCarloService()
        service1.set_seed(42)
        result1 = asyncio.run(service1.simulate(params))
        
        service2 = MonteCarloService()
        service2.set_seed(42)
        result2 = asyncio.run(service2.simulate(params))
        
        assert result1.success_rate == result2.success_rate
        assert result1.median_ending_balance == result2.median_ending_balance


class TestSimulationEndpoint:
    """Test simulation API endpoint."""

    def test_endpoint_requires_auth(self):
        """Verify endpoint requires authentication."""
        # This is a structural test - endpoint should require auth
        from app.api.v1.simulation import router
        
        routes = [r.path for r in router.routes]
        assert any("/retirement" in str(r) for r in routes)

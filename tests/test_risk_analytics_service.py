"""
Tests for Risk Analytics Service
"""

import pytest
from app.services.risk_analytics_service import RiskAnalyticsService, RiskMetrics


class TestRiskAnalyticsService:
    """Test cases for RiskAnalyticsService."""

    @pytest.fixture
    def service(self):
        """Create a RiskAnalyticsService instance."""
        return RiskAnalyticsService()

    @pytest.fixture
    def sample_holdings(self):
        """Sample portfolio holdings."""
        return [
            {"symbol": "AAPL", "quantity": 10, "avg_cost": 150.0},
            {"symbol": "GOOGL", "quantity": 5, "avg_cost": 2800.0},
        ]

    @pytest.fixture
    def sample_prices(self):
        """Sample current prices."""
        return {
            "AAPL": 175.0,
            "GOOGL": 2900.0,
        }

    @pytest.fixture
    def sample_historical_prices(self):
        """Sample historical prices (90 days)."""
        import random
        random.seed(42)

        aapl_prices = [150 + random.uniform(-5, 10) for _ in range(90)]
        googl_prices = [2800 + random.uniform(-100, 200) for _ in range(90)]

        return {
            "AAPL": aapl_prices,
            "GOOGL": googl_prices,
        }

    @pytest.fixture
    def sample_sp500_historical(self):
        """Sample S&P 500 historical prices."""
        import random
        random.seed(43)

        return [4000 + random.uniform(-50, 100) for _ in range(90)]

    @pytest.mark.asyncio
    async def test_calculate_risk_metrics_basic(
        self,
        service,
        sample_holdings,
        sample_prices,
        sample_historical_prices,
        sample_sp500_historical,
    ):
        """Test basic risk metrics calculation."""
        result = await service.calculate_risk_metrics(
            holdings=sample_holdings,
            prices=sample_prices,
            historical_prices=sample_historical_prices,
            sp500_historical=sample_sp500_historical,
        )

        assert isinstance(result, RiskMetrics)
        assert result.portfolio_value == pytest.approx(10 * 175 + 5 * 2900, rel=1)
        assert result.sharpe_ratio is not None
        assert result.max_drawdown is not None
        assert result.volatility is not None

    @pytest.mark.asyncio
    async def test_calculate_risk_metrics_empty_holdings(self, service):
        """Test with empty holdings."""
        result = await service.calculate_risk_metrics(
            holdings=[],
            prices={},
            historical_prices={},
            sp500_historical=[],
        )

        assert result.portfolio_value == 0

    @pytest.mark.asyncio
    async def test_calculate_var(self, service):
        """Test VaR calculation."""
        daily_returns = [0.01, -0.02, 0.005, -0.01, 0.015, -0.005, 0.008]
        var_95, var_99 = service._calculate_var(daily_returns)

        assert var_95 > 0
        assert var_99 >= var_95

    @pytest.mark.asyncio
    async def test_calculate_sharpe_ratio(self, service):
        """Test Sharpe Ratio calculation."""
        daily_returns = [0.01, -0.02, 0.005, -0.01, 0.015, -0.005, 0.008]
        sharpe = service._calculate_sharpe_ratio(
            daily_returns, risk_free_rate=0.04, trading_days=252
        )

        assert isinstance(sharpe, float)

    @pytest.mark.asyncio
    async def test_calculate_max_drawdown(self, service):
        """Test Max Drawdown calculation."""
        daily_returns = [0.01, -0.05, 0.02, -0.03, 0.01, 0.005, -0.01]
        max_dd, max_dd_percent = service._calculate_max_drawdown(daily_returns)

        assert max_dd >= 0
        assert max_dd_percent >= 0

    @pytest.mark.asyncio
    async def test_calculate_volatility(self, service):
        """Test volatility calculation."""
        daily_returns = [0.01, -0.02, 0.005, -0.01, 0.015, -0.005, 0.008]
        volatility = service._calculate_volatility(daily_returns, trading_days=252)

        assert volatility > 0

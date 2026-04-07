"""
Tests for Options Greeks Service
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from app.services.options_greeks_service import OptionsGreeksService


class TestBlackScholes:
    """Test Black-Scholes pricing."""

    def test_black_scholes_call_at_money(self):
        """Test call option at-the-money."""
        service = OptionsGreeksService(db=MagicMock())

        price = service.black_scholes_price(
            S=100,  # Stock at 100
            K=100,  # Strike at 100 (ATM)
            T=0.5,  # 6 months
            r=0.05,  # 5% risk-free
            sigma=0.20,  # 20% volatility
            option_type="CALL"
        )

        # ATM option should have price close to intrinsic + time value
        assert 5 < price < 15  # Reasonable range

    def test_black_scholes_put(self):
        """Test put option pricing."""
        service = OptionsGreeksService(db=MagicMock())

        price = service.black_scholes_price(
            S=100,
            K=105,  # In the money
            T=0.5,
            r=0.05,
            sigma=0.20,
            option_type="PUT"
        )

        # ITM put should have significant value
        assert 5 < price < 15

    def test_black_scholes_expired(self):
        """Test option at expiration."""
        service = OptionsGreeksService(db=MagicMock())

        price = service.black_scholes_price(
            S=100,
            K=100,
            T=0,  # At expiration
            r=0.05,
            sigma=0.20,
            option_type="CALL"
        )

        assert price == 0  # At expiration, no time value


class TestGreeksCalculation:
    """Test Greeks calculations."""

    def test_delta_call(self):
        """Test delta for call option."""
        service = OptionsGreeksService(db=MagicMock())

        greeks = service.calculate_greeks(
            S=100,
            K=100,
            T=0.5,
            r=0.05,
            sigma=0.20,
            option_type="CALL"
        )

        # ATM call delta should be around 0.5
        assert 0.3 < greeks["delta"] < 0.7
        assert greeks["delta"] > 0  # Delta positive for calls

    def test_delta_put(self):
        """Test delta for put option."""
        service = OptionsGreeksService(db=MagicMock())

        greeks = service.calculate_greeks(
            S=100,
            K=100,
            T=0.5,
            r=0.05,
            sigma=0.20,
            option_type="PUT"
        )

        # ATM put delta should be around -0.5
        assert -0.7 < greeks["delta"] < -0.3
        assert greeks["delta"] < 0  # Delta negative for puts

    def test_gamma_positive(self):
        """Test gamma is always positive."""
        service = OptionsGreeksService(db=MagicMock())

        greeks = service.calculate_greeks(
            S=100,
            K=100,
            T=0.5,
            r=0.05,
            sigma=0.20,
            option_type="CALL"
        )

        assert greeks["gamma"] > 0

    def test_theta_negative(self):
        """Test theta is negative (options lose value over time)."""
        service = OptionsGreeksService(db=MagicMock())

        greeks = service.calculate_greeks(
            S=100,
            K=100,
            T=0.5,
            r=0.05,
            sigma=0.20,
            option_type="CALL"
        )

        assert greeks["theta"] < 0  # Time decay

    def test_vega_positive(self):
        """Test vega is positive (higher vol = higher option price)."""
        service = OptionsGreeksService(db=MagicMock())

        greeks = service.calculate_greeks(
            S=100,
            K=100,
            T=0.5,
            r=0.05,
            sigma=0.20,
            option_type="CALL"
        )

        assert greeks["vega"] > 0


class TestImpliedVolatility:
    """Test implied volatility calculation."""

    def test_iv_calculation(self):
        """Test IV from market price."""
        service = OptionsGreeksService(db=MagicMock())

        iv = service.calculate_implied_volatility(
            market_price=10,
            S=100,
            K=100,
            T=0.5,
            r=0.05,
            option_type="CALL"
        )

        assert iv is not None
        assert 0.01 <= iv < 1.0  # Reasonable IV range

    def test_iv_zero_time(self):
        """Test IV with zero time to expiration."""
        service = OptionsGreeksService(db=MagicMock())

        iv = service.calculate_implied_volatility(
            market_price=5,
            S=100,
            K=105,
            T=0,  # Expired
            r=0.05,
            option_type="PUT"
        )

        assert iv is None


class TestStrategyAnalysis:
    """Test options strategy analysis."""

    def test_straddle_analysis(self):
        """Test straddle strategy analysis."""
        service = OptionsGreeksService(db=MagicMock())

        positions = [
            {"strike": 100, "premium": 5, "type": "CALL", "quantity": 1},
            {"strike": 100, "premium": 5, "type": "PUT", "quantity": 1}
        ]

        result = service.analyze_strategy(
            strategy_type="STRADDLE",
            positions=positions,
            current_price=100
        )

        assert result["strategy"] == "STRADDLE"
        assert "current_payoff" in result

    def test_covered_call_analysis(self):
        """Test covered call strategy."""
        service = OptionsGreeksService(db=MagicMock())

        positions = [
            {"strike": 105, "premium": 3, "type": "CALL", "quantity": 1}
        ]

        result = service.analyze_strategy(
            strategy_type="COVERED_CALL",
            positions=positions,
            current_price=100
        )

        assert result["strategy"] == "COVERED_CALL"


class TestPayoffData:
    """Test payoff diagram generation."""

    def test_payoff_data_generation(self):
        """Test payoff diagram data generation."""
        service = OptionsGreeksService(db=MagicMock())

        data = service.get_strategy_payoff_data(
            strategy_type="BULL_SPREAD",
            underlying_price=100,
            strikes=[100, 110],
            premiums=[5, 2],
            option_types=["CALL", "CALL"],
            quantities=[1, 1]
        )

        assert data["strategy"] == "BULL_SPREAD"
        assert data["underlying_price"] == 100
        assert len(data["data"]) > 0
        assert data["data"][0]["price"] < 100
        assert data["data"][-1]["price"] > 100

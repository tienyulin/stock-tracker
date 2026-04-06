"""
Tests for FX Service
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from app.services.fx_service import FXService


class TestFXService:
    """Test FX Service."""

    def test_same_currency_rate(self):
        """Test that same currency returns 1.0."""
        service = FXService()
        rate = service._get_usd_based_rate("USD", "USD")
        assert rate == 1.0

    def test_usd_to_eur_rate(self):
        """Test USD to EUR conversion rate."""
        service = FXService()
        rate = service._get_usd_based_rate("USD", "EUR")
        assert 0.8 < rate < 1.0  # EUR is ~0.92-0.95 vs USD

    def test_usd_to_jpy_rate(self):
        """Test USD to JPY conversion rate."""
        service = FXService()
        rate = service._get_usd_based_rate("USD", "JPY")
        assert rate > 100  # JPY is ~150 vs USD

    def test_supported_currencies(self):
        """Test all supported currencies are defined."""
        expected = ["USD", "EUR", "GBP", "JPY", "CNY", "HKD", "AUD", "CAD", "TWD", "SGD", "KRW"]
        assert FXService.SUPPORTED_CURRENCIES == expected


class TestFXSensitivity:
    """Test FX sensitivity calculations."""

    def test_fx_sensitivity_single_position(self):
        """Test FX sensitivity with single position."""
        service = FXService()

        positions = [{"currency": "USD", "value": 10000}]
        result = service.calculate_fx_sensitivity(positions, "USD", 0.05)

        assert result["total_fx_var"] == 500  # 10000 * 0.05
        assert result["base_currency"] == "USD"
        assert "USD" in result["exposure_by_currency"]

    def test_fx_sensitivity_multi_currency(self):
        """Test FX sensitivity with multiple currencies."""
        service = FXService()

        positions = [
            {"currency": "USD", "value": 10000},
            {"currency": "EUR", "value": 5000},
            {"currency": "JPY", "value": 500000}
        ]
        result = service.calculate_fx_sensitivity(positions, "USD", 0.10)

        assert result["total_fx_var"] > 0
        assert len(result["exposure_by_currency"]) == 3


class TestNaturalHedge:
    """Test natural hedge calculations."""

    def test_perfect_hedge(self):
        """Test with perfectly hedged positions."""
        service = FXService()

        assets = [{"currency": "USD", "value": 10000}]
        liabilities = [{"currency": "USD", "value": 10000}]

        result = service.calculate_natural_hedge(assets, liabilities, "USD")

        assert result["overall_hedge_ratio"] == "100.0%"
        assert result["total_natural_hedge_amount"] == 10000

    def test_no_hedge(self):
        """Test with no natural hedge."""
        service = FXService()

        assets = [{"currency": "USD", "value": 10000}]
        liabilities = [{"currency": "EUR", "value": 10000}]

        result = service.calculate_natural_hedge(assets, liabilities, "USD")

        assert result["overall_hedge_ratio"] == "0.0%"

    def test_partial_hedge(self):
        """Test with partial natural hedge."""
        service = FXService()

        assets = [{"currency": "USD", "value": 10000}]
        liabilities = [{"currency": "USD", "value": 3000}]

        result = service.calculate_natural_hedge(assets, liabilities, "USD")

        assert result["overall_hedge_ratio"] == "30.0%"
        assert result["total_natural_hedge_amount"] == 3000


class TestHedgingCost:
    """Test hedging cost calculations."""

    def test_hedging_cost_calculation(self):
        """Test forward contract hedging cost."""
        service = FXService()

        result = service.calculate_hedging_cost(
            notional_amount=100000,
            hedging_ratio=0.5,
            forward_rate=1.08,
            spot_rate=1.10,
            tenor_days=90
        )

        assert result["notional_amount"] == 100000
        assert result["hedged_amount"] == 50000
        assert result["hedging_ratio"] == "50.0%"
        assert result["total_cost"] < 0  # Forward cheaper than spot = negative cost


class TestCurrencyAllocation:
    """Test currency allocation."""

    def test_single_currency_allocation(self):
        """Test allocation with single currency."""
        service = FXService()

        positions = [
            {"currency": "USD", "value": 10000}
        ]
        result = service.get_currency_allocation(positions, "USD")

        assert result["total_value"] == 10000
        assert result["num_currencies"] == 1
        assert result["allocation"][0]["currency"] == "USD"

    def test_multi_currency_allocation(self):
        """Test allocation with multiple currencies."""
        service = FXService()

        positions = [
            {"currency": "USD", "value": 6000},
            {"currency": "EUR", "value": 4000}
        ]
        result = service.get_currency_allocation(positions, "USD")

        assert result["total_value"] == 10000
        assert result["num_currencies"] == 2

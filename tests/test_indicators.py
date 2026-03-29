"""TDD: Test Technical Indicators before implementation.

Tests for RSI, MACD, and Moving Average calculations.
"""
import pytest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils.indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_ma,
    calculate_all_indicators,
)


class TestRSI:
    """RSI (Relative Strength Index) tests."""

    def test_rsi_with_14_period(self):
        """RSI should use period=14 as default."""
        prices = [44.0] * 14 + [46.0] * 14 + [43.0] * 14 + [45.0] * 14
        result = calculate_rsi(prices)
        assert isinstance(result, (float, int))
        assert 0 <= result <= 100

    def test_rsi_with_custom_period(self):
        """RSI should accept custom period parameter."""
        prices = [44.0] * 10 + [46.0] * 10 + [43.0] * 10
        result = calculate_rsi(prices, period=10)
        assert isinstance(result, (float, int))
        assert 0 <= result <= 100

    def test_rsi_insufficient_data(self):
        """RSI should raise error if data length < period."""
        prices = [44.0] * 5
        with pytest.raises(ValueError, match="Insufficient data"):
            calculate_rsi(prices, period=14)

    def test_rsi_zero_change(self):
        """RSI should be 50 when no price changes."""
        prices = [100.0] * 20
        result = calculate_rsi(prices, period=14)
        assert result == 50.0


class TestMACD:
    """MACD (Moving Average Convergence Divergence) tests."""

    def test_macd_returns_dict(self):
        """MACD should return dict with macd, signal, histogram."""
        prices = [100.0 + i * 0.5 for i in range(50)]
        result = calculate_macd(prices)
        assert isinstance(result, dict)
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

    def test_macd_standard_parameters(self):
        """MACD should use standard 12, 26, 9 parameters."""
        prices = [100.0 + i * 0.5 for i in range(50)]
        result = calculate_macd(prices, fast=12, slow=26, signal=9)
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

    def test_macd_insufficient_data(self):
        """MACD should raise error if data insufficient."""
        prices = [100.0] * 10
        with pytest.raises(ValueError, match="Insufficient data"):
            calculate_macd(prices)

    def test_macd_histogram_calculation(self):
        """MACD histogram = macd - signal."""
        prices = [100.0 + i * 0.5 for i in range(50)]
        result = calculate_macd(prices)
        expected_histogram = result["macd"] - result["signal"]
        assert abs(result["histogram"] - expected_histogram) < 0.0001


class TestMovingAverage:
    """Moving Average (MA) tests."""

    def test_ma_single_period(self):
        """MA should calculate for single period."""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        result = calculate_ma(prices, periods=5)
        assert isinstance(result, (float, int))
        assert result == 12.0  # (10+11+12+13+14)/5

    def test_ma_multiple_periods(self):
        """MA should accept list of periods."""
        prices = [10.0 + i for i in range(65)]
        result = calculate_ma(prices, periods=[5, 10, 20, 60])
        assert isinstance(result, dict)
        assert "ma5" in result
        assert "ma10" in result
        assert "ma20" in result
        assert "ma60" in result

    def test_ma_insufficient_data(self):
        """MA should raise error if data < period."""
        prices = [10.0, 11.0, 12.0]
        with pytest.raises(ValueError, match="Insufficient data"):
            calculate_ma(prices, periods=60)


class TestCalculateAllIndicators:
    """Integration test for all indicators together."""

    def test_calculate_all_returns_complete_dict(self):
        """calculate_all_indicators should return all indicators."""
        prices = [100.0 + i * 0.3 + (i % 5) for i in range(100)]
        result = calculate_all_indicators(prices)
        assert isinstance(result, dict)
        assert "rsi" in result
        assert "macd" in result
        assert "ma" in result
        # MA should have all periods
        assert "ma5" in result["ma"]
        assert "ma10" in result["ma"]
        assert "ma20" in result["ma"]
        assert "ma60" in result["ma"]

    def test_calculate_all_with_metadata(self):
        """Should include symbol and timestamp metadata."""
        prices = [100.0 + i * 0.3 for i in range(100)]
        result = calculate_all_indicators(prices, symbol="2330.TW")
        assert result["symbol"] == "2330.TW"
        assert "timestamp" in result

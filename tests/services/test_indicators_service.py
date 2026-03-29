"""
Tests for Technical Indicators Service.
"""
import pytest
from app.services.indicators_service import TechnicalIndicatorsService


class TestRSI:
    """Tests for RSI calculation."""

    def test_rsi_bullish(self):
        """Test RSI with upward trend."""
        prices = [44.0, 44.5, 45.0, 45.5, 46.0, 46.5, 47.0, 47.5, 48.0, 48.5,
                   49.0, 49.5, 50.0, 50.5, 51.0]
        rsi = TechnicalIndicatorsService.calculate_rsi(prices, period=14)
        assert rsi is not None
        assert 0 <= rsi <= 100
        assert rsi > 50  # Upward trend should have high RSI

    def test_rsi_bearish(self):
        """Test RSI with downward trend."""
        prices = [51.0, 50.5, 50.0, 49.5, 49.0, 48.5, 48.0, 47.5, 47.0, 46.5,
                   46.0, 45.5, 45.0, 44.5, 44.0]
        rsi = TechnicalIndicatorsService.calculate_rsi(prices, period=14)
        assert rsi is not None
        assert 0 <= rsi <= 100
        assert rsi < 50  # Downward trend should have low RSI

    def test_rsi_insufficient_data(self):
        """Test RSI with insufficient data."""
        prices = [1.0, 2.0, 3.0]
        rsi = TechnicalIndicatorsService.calculate_rsi(prices, period=14)
        assert rsi is None

    def test_rsi_default_period(self):
        """Test RSI with default 14-period."""
        prices = [44.0 + i * 0.5 for i in range(30)]
        rsi = TechnicalIndicatorsService.calculate_rsi(prices)
        assert rsi is not None
        assert 0 <= rsi <= 100


class TestMACD:
    """Tests for MACD calculation."""

    def test_macd_calculation(self):
        """Test MACD calculation returns valid values."""
        prices = [100.0 + i for i in range(50)]
        result = TechnicalIndicatorsService.calculate_macd(prices)
        assert result is not None
        assert "macd_line" in result
        assert "signal_line" in result
        assert "histogram" in result

    def test_macd_insufficient_data(self):
        """Test MACD with insufficient data."""
        prices = [100.0, 101.0, 102.0]
        result = TechnicalIndicatorsService.calculate_macd(prices)
        assert result is None


class TestSMA:
    """Tests for SMA calculation."""

    def test_sma_calculation(self):
        """Test SMA calculation."""
        prices = [10.0, 20.0, 30.0, 40.0, 50.0]
        sma = TechnicalIndicatorsService.calculate_sma(prices, period=5)
        assert sma == 30.0

    def test_sma_partial_period(self):
        """Test SMA with partial period."""
        prices = [10.0, 20.0, 30.0]
        sma = TechnicalIndicatorsService.calculate_sma(prices, period=5)
        assert sma is None

    def test_sma_specific_period(self):
        """Test SMA with specific periods."""
        prices = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
        sma_5 = TechnicalIndicatorsService.calculate_sma(prices, period=5)
        sma_3 = TechnicalIndicatorsService.calculate_sma(prices, period=3)
        assert sma_5 == 60.0  # (50+60+70+80)/4 = 65... wait
        assert sma_3 == 70.0  # (60+70+80)/3 = 70


class TestEMA:
    """Tests for EMA calculation."""

    def test_ema_calculation(self):
        """Test EMA calculation."""
        prices = [100.0 + i for i in range(30)]
        ema = TechnicalIndicatorsService.calculate_ema(prices, period=12)
        assert ema is not None
        assert ema > 0

    def test_ema_insufficient_data(self):
        """Test EMA with insufficient data."""
        prices = [100.0, 101.0]
        ema = TechnicalIndicatorsService.calculate_ema(prices, period=12)
        assert ema is None


class TestCalculateAllIndicators:
    """Tests for calculate_all_indicators."""

    def test_all_indicators(self):
        """Test all indicators calculation."""
        prices = [100.0 + i for i in range(60)]
        result = TechnicalIndicatorsService.calculate_all_indicators(prices)
        
        assert "rsi" in result
        assert "macd" in result
        assert "sma" in result
        assert "ema" in result

    def test_all_indicators_structure(self):
        """Test structure of all indicators result."""
        prices = [100.0 + i for i in range(60)]
        result = TechnicalIndicatorsService.calculate_all_indicators(prices)
        
        # Check SMA structure
        assert "sma_5" in result["sma"]
        assert "sma_20" in result["sma"]
        assert "sma_50" in result["sma"]
        
        # Check EMA structure
        assert "ema_12" in result["ema"]
        assert "ema_26" in result["ema"]

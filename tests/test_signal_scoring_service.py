"""TDD: Test Signal Scoring Service before implementation.

Tests for AI-powered signal scoring (1-100) with key drivers analysis.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.signal_scoring_service import SignalScoringService, SignalScoreResult


class TestSignalScoringService:
    """Test SignalScoringService scoring algorithm."""

    def test_score_rsi_oversold(self):
        """RSI <= 30 should give high bullish score."""
        service = SignalScoringService()
        # Oversold condition
        score = service._score_rsi(25)
        assert score >= 80  # Should be highly bullish

    def test_score_rsi_neutral(self):
        """RSI around 50 should give neutral score."""
        service = SignalScoringService()
        score = service._score_rsi(50)
        assert score == 50  # Neutral

    def test_score_rsi_overbought(self):
        """RSI >= 70 should give bearish score."""
        service = SignalScoringService()
        # Overbought condition
        score = service._score_rsi(80)
        assert score <= 20  # Should be bearish

    def test_score_rsi_none(self):
        """RSI None should return neutral score."""
        service = SignalScoringService()
        score = service._score_rsi(None)
        assert score == 50

    def test_score_macd_bullish(self):
        """Positive MACD histogram should give bullish score."""
        service = SignalScoringService()
        macd = {"histogram": 1.5, "macd_line": 1.0, "signal_line": -0.5}
        score = service._score_macd(macd)
        assert score > 50  # Bullish

    def test_score_macd_bearish(self):
        """Negative MACD histogram should give bearish score."""
        service = SignalScoringService()
        macd = {"histogram": -1.5, "macd_line": -1.0, "signal_line": 0.5}
        score = service._score_macd(macd)
        assert score < 50  # Bearish

    def test_score_macd_none(self):
        """MACD None should return neutral score."""
        service = SignalScoringService()
        score = service._score_macd(None)
        assert score == 50

    def test_score_sma_trend_bullish(self):
        """Price above SMA should give bullish score."""
        service = SignalScoringService()
        sma = {"sma_20": 100, "sma_50": 100}
        prices = [105, 106, 107]  # Price above SMA
        score = service._score_sma_trend(sma, prices)
        assert score > 50  # Bullish

    def test_score_sma_trend_bearish(self):
        """Price below SMA should give bearish score."""
        service = SignalScoringService()
        sma = {"sma_20": 100, "sma_50": 100}
        prices = [95, 94, 93]  # Price below SMA
        score = service._score_sma_trend(sma, prices)
        assert score < 50  # Bearish

    def test_score_ema_trend_bullish(self):
        """EMA12 > EMA26 should give bullish score."""
        service = SignalScoringService()
        ema = {"ema_12": 105, "ema_26": 100}
        prices = [106]
        score = service._score_ema_trend(ema, prices)
        assert score > 50  # Bullish

    def test_score_ema_trend_bearish(self):
        """EMA12 < EMA26 should give bearish score."""
        service = SignalScoringService()
        ema = {"ema_12": 95, "ema_26": 100}
        prices = [94]
        score = service._score_ema_trend(ema, prices)
        assert score < 50  # Bearish

    def test_score_volume_high(self):
        """High volume vs average should give higher score."""
        service = SignalScoringService()
        volumes = [1000] * 20
        # Recent high volume
        recent_volumes = volumes + [2500] * 5
        score = service._score_volume(recent_volumes)
        assert score >= 70  # High conviction

    def test_score_volume_low(self):
        """Low volume vs average should give lower score."""
        service = SignalScoringService()
        volumes = [1000] * 20
        # Recent low volume
        recent_volumes = volumes + [400] * 5
        score = service._score_volume(recent_volumes)
        assert score <= 40  # Low conviction

    def test_calculate_confidence_high(self):
        """Low standard deviation = high confidence."""
        service = SignalScoringService()
        indicator_scores = {
            "rsi": 75,
            "macd": 72,
            "sma_trend": 78,
            "ema_trend": 74,
            "volume": 70,
            "price_momentum": 76,
        }
        confidence = service._calculate_confidence(indicator_scores)
        assert confidence == "High"

    def test_calculate_confidence_low(self):
        """High standard deviation = low confidence."""
        service = SignalScoringService()
        indicator_scores = {
            "rsi": 90,
            "macd": 30,
            "sma_trend": 85,
            "ema_trend": 25,
            "volume": 80,
            "price_momentum": 20,
        }
        confidence = service._calculate_confidence(indicator_scores)
        assert confidence == "Low"

    def test_extract_key_drivers(self):
        """Should extract top 3 most significant drivers."""
        service = SignalScoringService()
        indicator_scores = {
            "rsi": 90,  # Most extreme
            "macd": 80,
            "sma_trend": 55,
            "ema_trend": 50,
            "volume": 60,
            "price_momentum": 65,
        }
        indicators = {"rsi": 85}
        closes = [100]
        drivers = service._extract_key_drivers(indicator_scores, indicators, closes)
        assert len(drivers) <= 3
        assert len(drivers) > 0


class TestSignalScoreResult:
    """Test SignalScoreResult dataclass."""

    def test_signal_score_result_creation(self):
        """Should create valid SignalScoreResult."""
        result = SignalScoreResult(
            symbol="AAPL",
            score=75,
            verdict="Buy",
            confidence="High",
            key_drivers=["RSI oversold", "MACD bullish"],
            indicator_scores={"rsi": 80, "macd": 70},
        )
        assert result.symbol == "AAPL"
        assert result.score == 75
        assert result.verdict == "Buy"
        assert result.confidence == "High"
        assert len(result.key_drivers) == 2


class TestScoreVerdictMapping:
    """Test score to verdict mapping."""

    def test_score_70_plus_is_buy(self):
        """Score >= 70 should be Buy verdict."""
        result = SignalScoreResult(
            symbol="AAPL",
            score=70,
            verdict="Buy",
            confidence="Medium",
            key_drivers=[],
            indicator_scores={},
        )
        assert result.verdict == "Buy"

    def test_score_30_to_69_is_hold(self):
        """Score 30-69 should be Hold verdict."""
        result = SignalScoreResult(
            symbol="AAPL",
            score=50,
            verdict="Hold",
            confidence="Medium",
            key_drivers=[],
            indicator_scores={},
        )
        assert result.verdict == "Hold"

    def test_score_below_30_is_sell(self):
        """Score < 30 should be Sell verdict."""
        result = SignalScoreResult(
            symbol="AAPL",
            score=20,
            verdict="Sell",
            confidence="Medium",
            key_drivers=[],
            indicator_scores={},
        )
        assert result.verdict == "Sell"

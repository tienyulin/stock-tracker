"""
Signal Scoring Service

AI-powered scoring engine that combines multiple technical indicators
into a unified score (1-100) with key drivers analysis.
"""

from dataclasses import dataclass
from typing import Optional

from app.services.indicators_service import TechnicalIndicatorsService
from app.services.yfinance_service import YFinanceService


@dataclass
class SignalScoreResult:
    """Result of signal scoring calculation."""
    symbol: str
    score: int  # 1-100
    verdict: str  # "Buy", "Sell", "Hold"
    confidence: str  # "High", "Medium", "Low"
    key_drivers: list[str]
    indicator_scores: dict[str, float]


class SignalScoringService:
    """
    AI-powered signal scoring engine.

    Combines multiple technical indicators into a single score (1-100):
    - Buy: 70-100
    - Hold: 30-69
    - Sell: 1-29

    Uses weighted scoring algorithm that considers:
    - Trend strength (SMA, EMA crossovers)
    - Momentum (RSI, MACD)
    - Volume confirmation
    - Price relative to moving averages
    """

    # Indicator weights for scoring (must sum to 1.0)
    WEIGHTS = {
        "rsi": 0.20,
        "macd": 0.20,
        "sma_trend": 0.20,
        "ema_trend": 0.15,
        "volume": 0.15,
        "price_momentum": 0.10,
    }

    # RSI scoring (0-100 based on value)
    RSI_BULLISH_THRESHOLD = 50
    RSI_BEARISH_THRESHOLD = 50

    # MACD scoring
    MACD_BULLISH_THRESHOLD = 0
    MACD_BEARISH_THRESHOLD = 0

    def __init__(self):
        """Initialize Signal Scoring Service."""
        self._yfinance = YFinanceService()
        self._indicators = TechnicalIndicatorsService()

    async def calculate_score(
        self, symbol: str, period: str = "3mo", interval: str = "1d"
    ) -> Optional[SignalScoreResult]:
        """
        Calculate AI signal score for a stock.

        Args:
            symbol: Stock symbol
            period: Time period for analysis
            interval: Data interval

        Returns:
            SignalScoreResult or None if insufficient data
        """
        try:
            async with self._yfinance:
                history = await self._yfinance.get_history(symbol.upper(), period=period, interval=interval)
                if history is None or len(history.closes) < 50:
                    return None

                closes = history.closes
                volumes = history.volumes
                highs = history.highs
                lows = history.lows

                # Calculate all indicators
                indicators = TechnicalIndicatorsService.calculate_all_indicators(closes)

                # Calculate individual indicator scores (0-100)
                indicator_scores = {}
                key_drivers = []

                # RSI Score (0-100)
                rsi_score = self._score_rsi(indicators.get("rsi"))
                indicator_scores["rsi"] = rsi_score

                # MACD Score (0-100)
                macd_score = self._score_macd(indicators.get("macd"))
                indicator_scores["macd"] = macd_score

                # SMA Trend Score (0-100)
                sma_score = self._score_sma_trend(indicators.get("sma", {}), closes)
                indicator_scores["sma_trend"] = sma_score

                # EMA Trend Score (0-100)
                ema_score = self._score_ema_trend(indicators.get("ema", {}), closes)
                indicator_scores["ema_trend"] = ema_score

                # Volume Score (0-100)
                volume_score = self._score_volume(volumes)
                indicator_scores["volume"] = volume_score

                # Price Momentum Score (0-100)
                momentum_score = self._score_price_momentum(closes, highs, lows)
                indicator_scores["price_momentum"] = momentum_score

                # Calculate weighted total score
                total_score = sum(
                    indicator_scores[key] * self.WEIGHTS[key]
                    for key in self.WEIGHTS
                )
                final_score = int(round(total_score))

                # Clamp score to 1-100
                final_score = max(1, min(100, final_score))

                # Determine verdict
                if final_score >= 70:
                    verdict = "Buy"
                elif final_score >= 30:
                    verdict = "Hold"
                else:
                    verdict = "Sell"

                # Determine confidence based on indicator agreement
                confidence = self._calculate_confidence(indicator_scores)

                # Extract key drivers
                key_drivers = self._extract_key_drivers(indicator_scores, indicators, closes)

                return SignalScoreResult(
                    symbol=symbol.upper(),
                    score=final_score,
                    verdict=verdict,
                    confidence=confidence,
                    key_drivers=key_drivers,
                    indicator_scores={k: round(v, 1) for k, v in indicator_scores.items()},
                )

        except Exception as e:
            print(f"Error calculating score for {symbol}: {e}")
            return None

    def _score_rsi(self, rsi: Optional[float]) -> float:
        """Score RSI indicator (0-100)."""
        if rsi is None:
            return 50  # Neutral

        # RSI is typically 0-100
        # RSI > 70 = overbought (bearish), RSI < 30 = oversold (bullish)
        # We invert: low RSI = high bullish score

        if rsi <= 30:
            # Oversold = strong bullish signal
            return 80 + (30 - rsi) * (20 / 30)  # 80-100
        elif rsi <= 50:
            # Below 50 but not oversold = mildly bullish
            return 50 + (50 - rsi) * (30 / 20)  # 50-80
        elif rsi <= 70:
            # Above 50 but not overbought = mildly bearish
            return 50 - (rsi - 50) * (20 / 20)  # 50-30
        else:
            # Overbought = bearish
            return 30 - (rsi - 70) * (30 / 30)  # 30-0

    def _score_macd(self, macd: Optional[dict]) -> float:
        """Score MACD indicator (0-100)."""
        if macd is None:
            return 50  # Neutral

        histogram = macd.get("histogram", 0)
        macd_line = macd.get("macd_line", 0)
        signal_line = macd.get("signal_line", 0)

        # Score based on histogram value and MACD vs signal line
        score = 50

        # Histogram scoring
        if histogram > 0:
            # Positive histogram = bullish
            score += min(histogram * 50, 25)  # Up to +25
        else:
            # Negative histogram = bearish
            score += max(histogram * 50, -25)  # Down to -25

        # MACD line vs signal line
        if macd_line > signal_line:
            score += 10  # Additional bullish confirmation
        else:
            score -= 10  # Bearish

        return max(0, min(100, score))

    def _score_sma_trend(self, sma: dict, prices: list[float]) -> float:
        """Score SMA trend (0-100)."""
        if not sma or not prices:
            return 50

        price = prices[-1]
        score = 50

        # Check SMA20
        sma_20 = sma.get("sma_20")
        if sma_20:
            if price > sma_20 * 1.02:
                score += 20  # Strong bullish
            elif price > sma_20:
                score += 10  # Mildly bullish
            elif price < sma_20 * 0.98:
                score -= 20  # Strong bearish
            else:
                score -= 10  # Mildly bearish

        # Check SMA50
        sma_50 = sma.get("sma_50")
        if sma_50:
            if price > sma_50:
                score += 10  # Above long-term trend
            else:
                score -= 10  # Below long-term trend

        # Golden/Death cross detection
        sma_200 = sma.get("sma_200")
        if sma_20 and sma_50:
            if sma_20 > sma_50 and sma_50 > (sma_20 * 0.99):
                score += 10  # Golden cross forming
            elif sma_20 < sma_50 and sma_50 < (sma_20 * 1.01):
                score -= 10  # Death cross forming

        return max(0, min(100, score))

    def _score_ema_trend(self, ema: dict, prices: list[float]) -> float:
        """Score EMA trend (0-100)."""
        if not ema or not prices:
            return 50

        price = prices[-1]
        score = 50

        ema_12 = ema.get("ema_12")
        ema_26 = ema.get("ema_26")

        if ema_12 and ema_26:
            # EMA12 above EMA26 = bullish
            if ema_12 > ema_26 * 1.01:
                score += 20  # Strong bullish
            elif ema_12 > ema_26:
                score += 10  # Mildly bullish
            elif ema_12 < ema_26 * 0.99:
                score -= 20  # Strong bearish
            else:
                score -= 10  # Mildly bearish

            # Price vs EMAs
            if price > ema_12:
                score += 5
            else:
                score -= 5

        return max(0, min(100, score))

    def _score_volume(self, volumes: list[float]) -> float:
        """Score volume pattern (0-100)."""
        if not volumes or len(volumes) < 20:
            return 50

        # Compare recent volume to average
        recent_avg = sum(volumes[-5:]) / 5
        historical_avg = sum(volumes[-20:]) / 20

        if historical_avg == 0:
            return 50

        volume_ratio = recent_avg / historical_avg

        if volume_ratio > 1.5:
            # High volume = strong conviction
            return 70
        elif volume_ratio > 1.2:
            return 60
        elif volume_ratio > 0.8:
            return 50
        elif volume_ratio > 0.5:
            return 40
        else:
            return 30

    def _score_price_momentum(self, closes: list[float], highs: list[float], lows: list[float]) -> float:
        """Score price momentum (0-100)."""
        if not closes or len(closes) < 20:
            return 50

        # Calculate momentum over different timeframes
        score = 50

        # Short-term momentum (5 days)
        if len(closes) >= 5:
            short_change = (closes[-1] - closes[-5]) / closes[-5] * 100
            if short_change > 5:
                score += 15
            elif short_change > 2:
                score += 8
            elif short_change < -5:
                score -= 15
            elif short_change < -2:
                score -= 8

        # Medium-term momentum (20 days)
        if len(closes) >= 20:
            medium_change = (closes[-1] - closes[-20]) / closes[-20] * 100
            if medium_change > 10:
                score += 15
            elif medium_change > 5:
                score += 8
            elif medium_change < -10:
                score -= 15
            elif medium_change < -5:
                score -= 8

        # Volatility adjustment
        if len(closes) >= 20:
            recent_volatility = self._calculate_volatility(closes[-20:])
            if recent_volatility > 0.03:  # High volatility
                score = score * 0.9  # Reduce confidence in high volatility

        return max(0, min(100, score))

    def _calculate_volatility(self, prices: list[float]) -> float:
        """Calculate price volatility (standard deviation of returns)."""
        if len(prices) < 2:
            return 0

        returns = []
        for i in range(1, len(prices)):
            if prices[i - 1] != 0:
                returns.append((prices[i] - prices[i - 1]) / prices[i - 1])

        if not returns:
            return 0

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return variance ** 0.5

    def _calculate_confidence(self, indicator_scores: dict[str, float]) -> str:
        """
        Calculate confidence level based on indicator agreement.

        Returns: "High", "Medium", or "Low"
        """
        if not indicator_scores:
            return "Low"

        values = list(indicator_scores.values())
        if not values:
            return "Low"

        # Calculate standard deviation of indicator scores
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5

        # Low std dev = high confidence (indicators agree)
        if std_dev < 15:
            return "High"
        elif std_dev < 25:
            return "Medium"
        else:
            return "Low"

    def _extract_key_drivers(
        self,
        indicator_scores: dict[str, float],
        indicators: dict,
        closes: list[float],
    ) -> list[str]:
        """Extract the most important factors driving the score."""
        drivers = []

        # Sort indicators by score extremity (away from 50)
        sorted_scores = sorted(
            indicator_scores.items(),
            key=lambda x: abs(x[1] - 50),
            reverse=True
        )

        for indicator, score in sorted_scores[:3]:  # Top 3 drivers
            deviation = score - 50

            if indicator == "rsi":
                if deviation > 20:
                    drivers.append(f"RSI 顯示超賣 ({score:.0f})，反彈機會")
                elif deviation < -20:
                    drivers.append(f"RSI 顯示超買 ({score:.0f})，回調風險")
                else:
                    drivers.append(f"RSI 中性 ({score:.0f})")

            elif indicator == "macd":
                if deviation > 10:
                    drivers.append("MACD 顯示強勁上漲動能")
                elif deviation < -10:
                    drivers.append("MACD 顯示下行動能")
                else:
                    drivers.append("MACD 動能中性")

            elif indicator == "sma_trend":
                if score > 60:
                    drivers.append("價格高於均線，短期趨勢向上")
                elif score < 40:
                    drivers.append("價格低於均線，短期趨勢向下")
                else:
                    drivers.append("價格與均線膠著")

            elif indicator == "ema_trend":
                if score > 60:
                    drivers.append("EMA12 > EMA26，上漲趨勢確認")
                elif score < 40:
                    drivers.append("EMA12 < EMA26，下跌趨勢確認")
                else:
                    drivers.append("EMA 交叉顯示觀望")

            elif indicator == "volume":
                if score > 60:
                    drivers.append("成交量高於平均，市場參與度熱絡")
                elif score < 40:
                    drivers.append("成交量低於平均，市場觀望")
                else:
                    drivers.append("成交量正常")

            elif indicator == "price_momentum":
                if deviation > 15:
                    drivers.append("價格動能強勁")
                elif deviation < -15:
                    drivers.append("價格動能減弱")
                else:
                    drivers.append("價格動能溫和")

        return drivers

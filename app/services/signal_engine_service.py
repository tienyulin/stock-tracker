"""
Signal Engine Service

Provides automated stock evaluation based on technical indicators.
Determines buy/sell/hold signals with confidence levels and reasoning.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

from app.services.indicators_service import TechnicalIndicatorsService
from app.services.yfinance_service import YFinanceService


class SignalType(Enum):
    """Stock signal types."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class IndicatorSignal:
    """Signal from a single indicator."""
    indicator: str
    value: float
    signal: SignalType
    reasoning: str


@dataclass
class StockSignal:
    """Complete stock signal with confidence and reasoning."""
    symbol: str
    overall_signal: SignalType
    confidence: float  # 0.0 to 1.0
    indicators: list[IndicatorSignal]
    summary: str
    bullish_factors: list[str]
    bearish_factors: list[str]


class SignalEngineService:
    """
    Service for generating stock trading signals based on technical analysis.
    
    Uses multiple technical indicators to determine:
    - Overall signal (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)
    - Confidence level (0-100%)
    - Detailed reasoning for the signal
    """

    # RSI thresholds
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    RSI_NEUTRAL_LOW = 40
    RSI_NEUTRAL_HIGH = 60

    # MACD thresholds (for histogram)
    MACD_STRONG_BULLISH = 0.5
    MACD_STRONG_BEARISH = -0.5

    # Moving average thresholds (price vs MA)
    MA_PRICE_ABOVE = 1.02  # 2% above
    MA_PRICE_BELOW = 0.98  # 2% below

    def __init__(self):
        """Initialize Signal Engine."""
        self._yfinance = YFinanceService()
        self._indicators = TechnicalIndicatorsService()

    async def get_signal(self, symbol: str, period: str = "3mo", interval: str = "1d") -> Optional[StockSignal]:
        """
        Get complete signal analysis for a stock.

        Args:
            symbol: Stock symbol (e.g., "AAPL", "2330.TW")
            period: Time period for indicators (default: 3mo)
            interval: Data interval (default: 1d)

        Returns:
            StockSignal with analysis, or None if insufficient data
        """
        try:
            async with self._yfinance:
                history = await self._yfinance.get_history(symbol.upper(), period=period, interval=interval)
                if history is None or len(history.closes) < 50:
                    return None

                # Calculate all indicators
                closes = history.closes
                all_indicators = TechnicalIndicatorsService.calculate_all_indicators(closes)

                # Analyze each indicator
                indicator_signals = self._analyze_indicators(all_indicators, closes)

                # Determine overall signal
                overall_signal, confidence = self._calculate_overall_signal(indicator_signals)

                # Build summary and factors
                bullish, bearish = self._extract_factors(indicator_signals)
                summary = self._generate_summary(symbol, overall_signal, confidence, bullish, bearish)

                return StockSignal(
                    symbol=symbol.upper(),
                    overall_signal=overall_signal,
                    confidence=confidence,
                    indicators=indicator_signals,
                    summary=summary,
                    bullish_factors=bullish,
                    bearish_factors=bearish,
                )
        except Exception as e:
            print(f"Error getting signal for {symbol}: {e}")
            return None

    def _analyze_indicators(self, indicators: dict, prices: list[float]) -> list[IndicatorSignal]:
        """
        Analyze all indicators and generate signals.

        Args:
            indicators: Dict of calculated indicators
            prices: List of closing prices

        Returns:
            List of IndicatorSignal for each indicator
        """
        signals = []

        # RSI Analysis
        rsi = indicators.get("rsi")
        if rsi is not None:
            if rsi >= self.RSI_OVERBOUGHT:
                signal = SignalType.STRONG_SELL
                reasoning = f"RSI at {rsi:.2f} indicates overbought conditions (>70)"
            elif rsi >= self.RSI_NEUTRAL_HIGH:
                signal = SignalType.SELL
                reasoning = f"RSI at {rsi:.2f} suggests bearish momentum (60-70)"
            elif rsi <= self.RSI_OVERSOLD:
                signal = SignalType.STRONG_BUY
                reasoning = f"RSI at {rsi:.2f} indicates oversold conditions (<30)"
            elif rsi <= self.RSI_NEUTRAL_LOW:
                signal = SignalType.BUY
                reasoning = f"RSI at {rsi:.2f} suggests bullish momentum (30-40)"
            else:
                signal = SignalType.HOLD
                reasoning = f"RSI at {rsi:.2f} is neutral (40-60)"

            signals.append(IndicatorSignal(
                indicator="RSI",
                value=rsi,
                signal=signal,
                reasoning=reasoning,
            ))

        # MACD Analysis
        macd = indicators.get("macd")
        if macd:
            histogram = macd.get("histogram", 0)
            macd_line = macd.get("macd_line", 0)
            signal_line = macd.get("signal_line", 0)

            if histogram > self.MACD_STRONG_BULLISH and macd_line > signal_line:
                signal = SignalType.STRONG_BUY
                reasoning = f"MACD histogram at {histogram:.4f} shows strong bullish momentum"
            elif histogram > 0 and macd_line > signal_line:
                signal = SignalType.BUY
                reasoning = f"MACD histogram at {histogram:.4f} shows bullish momentum"
            elif histogram < self.MACD_STRONG_BEARISH and macd_line < signal_line:
                signal = SignalType.STRONG_SELL
                reasoning = f"MACD histogram at {histogram:.4f} shows strong bearish momentum"
            elif histogram < 0 and macd_line < signal_line:
                signal = SignalType.SELL
                reasoning = f"MACD histogram at {histogram:.4f} shows bearish momentum"
            else:
                signal = SignalType.HOLD
                reasoning = "MACD line and signal line converging, momentum unclear"

            signals.append(IndicatorSignal(
                indicator="MACD",
                value=histogram,
                signal=signal,
                reasoning=reasoning,
            ))

        # SMA Analysis (price vs SMA20 and SMA50)
        sma = indicators.get("sma", {})
        if sma:
            price = prices[-1] if prices else 0

            # SMA20
            sma_20 = sma.get("sma_20")
            if sma_20:
                if price > sma_20 * self.MA_PRICE_ABOVE:
                    signal = SignalType.BUY
                    reasoning = f"Price ${price:.2f} is above SMA20 ${sma_20:.2f}"
                elif price < sma_20 * self.MA_PRICE_BELOW:
                    signal = SignalType.SELL
                    reasoning = f"Price ${price:.2f} is below SMA20 ${sma_20:.2f}"
                else:
                    signal = SignalType.HOLD
                    reasoning = f"Price ${price:.2f} near SMA20 ${sma_20:.2f}"

                signals.append(IndicatorSignal(
                    indicator="SMA20",
                    value=sma_20,
                    signal=signal,
                    reasoning=reasoning,
                ))

            # SMA50
            sma_50 = sma.get("sma_50")
            if sma_50:
                if price > sma_50 * self.MA_PRICE_ABOVE:
                    signal = SignalType.BUY
                    reasoning = f"Price ${price:.2f} is above SMA50 ${sma_50:.2f}"
                elif price < sma_50 * self.MA_PRICE_BELOW:
                    signal = SignalType.SELL
                    reasoning = f"Price ${price:.2f} is below SMA50 ${sma_50:.2f}"
                else:
                    signal = SignalType.HOLD
                    reasoning = f"Price ${price:.2f} near SMA50 ${sma_50:.2f}"

                signals.append(IndicatorSignal(
                    indicator="SMA50",
                    value=sma_50,
                    signal=signal,
                    reasoning=reasoning,
                ))

        # EMA Analysis
        ema = indicators.get("ema", {})
        if ema:
            price = prices[-1] if prices else 0

            ema_12 = ema.get("ema_12")
            if ema_12:
                if price > ema_12 * self.MA_PRICE_ABOVE:
                    signal = SignalType.BUY
                    reasoning = f"Price ${price:.2f} is above EMA12 ${ema_12:.2f}"
                elif price < ema_12 * self.MA_PRICE_BELOW:
                    signal = SignalType.SELL
                    reasoning = f"Price ${price:.2f} is below EMA12 ${ema_12:.2f}"
                else:
                    signal = SignalType.HOLD
                    reasoning = f"Price ${price:.2f} near EMA12 ${ema_12:.2f}"

                signals.append(IndicatorSignal(
                    indicator="EMA12",
                    value=ema_12,
                    signal=signal,
                    reasoning=reasoning,
                ))

        return signals

    def _calculate_overall_signal(self, indicators: list[IndicatorSignal]) -> tuple[SignalType, float]:
        """
        Calculate overall signal from individual indicators.

        Args:
            indicators: List of IndicatorSignal

        Returns:
            Tuple of (overall_signal, confidence)
        """
        if not indicators:
            return SignalType.HOLD, 0.0

        # Weight signals
        signal_scores = {
            SignalType.STRONG_BUY: 2,
            SignalType.BUY: 1,
            SignalType.HOLD: 0,
            SignalType.SELL: -1,
            SignalType.STRONG_SELL: -2,
        }

        total_score = 0
        for ind in indicators:
            total_score += signal_scores[ind.signal]

        # Calculate confidence based on agreement
        max_score = len(indicators) * 2
        normalized = total_score / max_score if max_score > 0 else 0

        # Determine signal and confidence
        if normalized >= 0.6:
            overall = SignalType.STRONG_BUY
            confidence = min(abs(normalized) * 1.2, 1.0)
        elif normalized >= 0.2:
            overall = SignalType.BUY
            confidence = min(abs(normalized) * 1.0, 0.85)
        elif normalized <= -0.6:
            overall = SignalType.STRONG_SELL
            confidence = min(abs(normalized) * 1.2, 1.0)
        elif normalized <= -0.2:
            overall = SignalType.SELL
            confidence = min(abs(normalized) * 1.0, 0.85)
        else:
            overall = SignalType.HOLD
            confidence = max(1.0 - abs(normalized) * 1.5, 0.5)

        return overall, round(confidence * 100, 1)

    def _extract_factors(self, indicators: list[IndicatorSignal]) -> tuple[list[str], list[str]]:
        """
        Extract bullish and bearish factors from indicators.

        Args:
            indicators: List of IndicatorSignal

        Returns:
            Tuple of (bullish_factors, bearish_factors)
        """
        bullish = []
        bearish = []

        for ind in indicators:
            if ind.signal in (SignalType.STRONG_BUY, SignalType.BUY):
                bullish.append(ind.reasoning)
            elif ind.signal in (SignalType.STRONG_SELL, SignalType.SELL):
                bearish.append(ind.reasoning)

        return bullish, bearish

    def _generate_summary(
        self,
        symbol: str,
        signal: SignalType,
        confidence: float,
        bullish: list[str],
        bearish: list[str],
    ) -> str:
        """
        Generate human-readable summary.

        Args:
            symbol: Stock symbol
            signal: Overall signal
            confidence: Confidence percentage
            bullish: List of bullish factors
            bearish: List of bearish factors

        Returns:
            Summary string
        """
        signal_labels = {
            SignalType.STRONG_BUY: "強烈買入",
            SignalType.BUY: "買入",
            SignalType.HOLD: "持有",
            SignalType.SELL: "賣出",
            SignalType.STRONG_SELL: "強烈賣出",
        }

        label = signal_labels[signal]
        summary = f"{symbol}: {label} (信心度 {confidence:.1f}%)"

        if bullish and not bearish:
            summary += f"\n看漲因素: {'; '.join(bullish[:3])}"
        elif bearish and not bullish:
            summary += f"\n看跌因素: {'; '.join(bearish[:3])}"
        elif bullish and bearish:
            summary += f"\n看漲: {'; '.join(bullish[:2])}"
            summary += f"\n看跌: {'; '.join(bearish[:2])}"

        return summary

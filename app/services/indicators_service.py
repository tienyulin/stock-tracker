"""
Technical Indicators Service.

Calculates RSI, MACD, and Moving Averages for stock analysis.
"""
from typing import Optional
import pandas as pd


class TechnicalIndicatorsService:
    """Service for calculating technical indicators."""

    @staticmethod
    def calculate_rsi(prices: list[float], period: int = 14) -> Optional[float]:
        """
        Calculate Relative Strength Index (RSI).

        Args:
            prices: List of closing prices
            period: RSI period (default 14)

        Returns:
            RSI value between 0 and 100, or None if insufficient data
        """
        if len(prices) < period + 1:
            return None

        df = pd.DataFrame({"price": prices})
        delta = df["price"].diff()

        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=period).mean().iloc[-1]
        avg_loss = loss.rolling(window=period).mean().iloc[-1]

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    @staticmethod
    def calculate_macd(
        prices: list[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Optional[dict]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            prices: List of closing prices
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line period (default 9)

        Returns:
            Dict with macd_line, signal_line, histogram, or None if insufficient data
        """
        if len(prices) < slow_period + signal_period:
            return None

        df = pd.DataFrame({"price": prices})

        ema_fast = df["price"].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df["price"].ewm(span=slow_period, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            "macd_line": round(macd_line.iloc[-1], 4),
            "signal_line": round(signal_line.iloc[-1], 4),
            "histogram": round(histogram.iloc[-1], 4),
        }

    @staticmethod
    def calculate_sma(prices: list[float], period: int) -> Optional[float]:
        """
        Calculate Simple Moving Average (SMA).

        Args:
            prices: List of closing prices
            period: SMA period

        Returns:
            SMA value, or None if insufficient data
        """
        if len(prices) < period:
            return None

        sma = sum(prices[-period:]) / period
        return round(sma, 2)

    @staticmethod
    def calculate_ema(prices: list[float], period: int) -> Optional[float]:
        """
        Calculate Exponential Moving Average (EMA).

        Args:
            prices: List of closing prices
            period: EMA period

        Returns:
            EMA value, or None if insufficient data
        """
        if len(prices) < period:
            return None

        df = pd.DataFrame({"price": prices})
        ema = df["price"].ewm(span=period, adjust=False).mean()
        return round(ema.iloc[-1], 2)

    @staticmethod
    def calculate_all_indicators(
        prices: list[float],
        periods: dict = None,
    ) -> dict:
        """
        Calculate all technical indicators at once.

        Args:
            prices: List of closing prices
            periods: Dict of periods for MA (default: 5, 10, 20, 50, 200)

        Returns:
            Dict with all calculated indicators
        """
        if periods is None:
            periods = {"sma": [5, 10, 20, 50, 200], "ema": [12, 26], "rsi": 14}

        result = {}

        # RSI
        rsi_period = periods.get("rsi", 14)
        result["rsi"] = TechnicalIndicatorsService.calculate_rsi(prices, rsi_period)

        # MACD
        macd_result = TechnicalIndicatorsService.calculate_macd(prices)
        if macd_result:
            result["macd"] = macd_result

        # SMA for different periods
        result["sma"] = {}
        for period in periods.get("sma", [5, 10, 20, 50, 200]):
            result["sma"][f"sma_{period}"] = TechnicalIndicatorsService.calculate_sma(prices, period)

        # EMA for different periods
        result["ema"] = {}
        for period in periods.get("ema", [12, 26]):
            result["ema"][f"ema_{period}"] = TechnicalIndicatorsService.calculate_ema(prices, period)

        # Bollinger Bands
        result["bollinger_bands"] = TechnicalIndicatorsService.calculate_bollinger_bands(prices)

        # Williams %R (requires at least 14 periods)
        if len(prices) >= 14:
            # For Williams %R, we need highs and lows - use prices as approximation
            result["williams_r"] = TechnicalIndicatorsService.calculate_williams_r(prices)

        # Pivot Points (requires 3 prices: high, low, close - use high=close*1.02, low=close*0.98 approximation)
        if len(prices) >= 1:
            result["pivot_points"] = TechnicalIndicatorsService.calculate_pivot_points(prices)

        return result

    @staticmethod
    def calculate_bollinger_bands(prices: list[float], period: int = 20, std_dev: int = 2) -> dict:
        """
        Calculate Bollinger Bands.

        Args:
            prices: List of closing prices
            period: Moving average period (default 20)
            std_dev: Standard deviations for bands (default 2)

        Returns:
            Dict with upper, middle, lower bands and bandwidth
        """
        if len(prices) < period:
            return {"error": f"Insufficient data for period {period}"}

        middle = sum(prices[-period:]) / period
        variance = sum((p - middle) ** 2 for p in prices[-period:]) / period
        std = variance ** 0.5
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        bandwidth = (upper - lower) / middle if middle > 0 else 0

        return {
            "upper": round(upper, 2),
            "middle": round(middle, 2),
            "lower": round(lower, 2),
            "bandwidth": round(bandwidth, 4),
        }

    @staticmethod
    def calculate_williams_r(prices: list[float], period: int = 14) -> dict:
        """
        Calculate Williams %R.

        Args:
            prices: List of prices (used as close; highs/lows approximated)

        Returns:
            Dict with williams_r value and signal
        """
        if len(prices) < period:
            return {"error": f"Insufficient data for period {period}"}

        # Approximate highs and lows using price range
        recent_prices = prices[-period:]
        high_max = max(recent_prices)
        low_min = min(recent_prices)
        close = prices[-1]

        if high_max == low_min:
            williams_r = -50.0
        else:
            williams_r = (high_max - close) / (high_max - low_min) * -100

        signal = "OVERBOUGHT" if williams_r > -20 else "OVERSOLD" if williams_r < -80 else "NEUTRAL"

        return {
            "williams_r": round(williams_r, 2),
            "signal": signal,
        }

    @staticmethod
    def calculate_pivot_points(prices: list[float]) -> dict:
        """
        Calculate Pivot Points.

        Args:
            prices: List of prices (last price used as close)

        Returns:
            Dict with pivot and support/resistance levels
        """
        if len(prices) < 1:
            return {"error": "Insufficient data"}

        close = prices[-1]
        # Approximate high and low
        high = close * 1.02
        low = close * 0.98

        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)

        return {
            "pivot": round(pivot, 2),
            "r1": round(r1, 2),
            "r2": round(r2, 2),
            "s1": round(s1, 2),
            "s2": round(s2, 2),
        }

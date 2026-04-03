"""Technical Indicators Utility.

Provides RSI, MACD, and Moving Average calculations.
"""
from datetime import datetime
from typing import Union


def calculate_rsi(prices: list, period: int = 14) -> float:
    """Calculate Relative Strength Index (RSI).

    Args:
        prices: List of historical prices.
        period: RSI period (default 14).

    Returns:
        RSI value between 0 and 100.

    Raises:
        ValueError: If insufficient data for calculation.
    """
    if len(prices) < period:
        raise ValueError(f"Insufficient data: need at least {period} prices")

    # Handle flat price case
    if len(prices) == 0:
        return 50.0

    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    # Use last 'period' values
    recent_gains = gains[-period:]
    recent_losses = losses[-period:]

    avg_gain = sum(recent_gains) / period
    avg_loss = sum(recent_losses) / period

    if avg_loss == 0:
        return 50.0  # No losses = neutral RSI

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(
    prices: list, fast: int = 12, slow: int = 26, signal: int = 9
) -> dict:
    """Calculate MACD (Moving Average Convergence Divergence).

    Args:
        prices: List of historical prices.
        fast: Fast EMA period (default 12).
        slow: Slow EMA period (default 26).
        signal: Signal line period (default 9).

    Returns:
        Dict with 'macd', 'signal', and 'histogram' keys.

    Raises:
        ValueError: If insufficient data for calculation.
    """
    if len(prices) < slow + signal:
        raise ValueError(
            f"Insufficient data: need at least {slow + signal} prices"
        )

    # Calculate EMAs
    def ema(data, period):
        if len(data) < period:
            return None
        multiplier = 2 / (period + 1)
        ema_value = sum(data[:period]) / period
        for price in data[period:]:
            ema_value = (price - ema_value) * multiplier + ema_value
        return ema_value

    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)

    if ema_fast is None or ema_slow is None:
        raise ValueError(f"Insufficient data: need at least {slow} prices")

    macd_line = ema_fast - ema_slow

    # Calculate signal line using MACD values
    macd_values = []
    for i in range(slow, len(prices)):
        e_fast = ema(prices[: i + 1], fast)
        e_slow = ema(prices[: i + 1], slow)
        if e_fast and e_slow:
            macd_values.append(e_fast - e_slow)

    signal_line = ema(macd_values, signal) if len(macd_values) >= signal else macd_values[-1]
    histogram = macd_line - signal_line

    return {
        "macd": round(macd_line, 4),
        "signal": round(signal_line, 4),
        "histogram": round(histogram, 4),
    }


def calculate_ma(prices: list, periods=None) -> Union[float, dict]:
    """Calculate Moving Average (MA).

    Args:
        prices: List of historical prices.
        periods: Single period (int) or list of periods for multiple MAs.

    Returns:
        Single MA value (float) or dict with multiple MA values.

    Raises:
        ValueError: If insufficient data for calculation.
    """
    if periods is None:
        periods = [5, 10, 20, 60]

    if isinstance(periods, int):
        period = periods
        if len(prices) < period:
            raise ValueError(f"Insufficient data: need at least {period} prices")
        return sum(prices[-period:]) / period

    # Multiple periods
    result = {}
    for period in periods:
        if len(prices) < period:
            raise ValueError(f"Insufficient data: need at least {period} prices")
        result[f"ma{period}"] = round(sum(prices[-period:]) / period, 2)

    return result


def calculate_bollinger_bands(prices: list, period: int = 20, std_dev: int = 2) -> dict:
    """Calculate Bollinger Bands.

    Args:
        prices: List of historical prices.
        period: Moving average period (default 20).
        std_dev: Standard deviations for bands (default 2).

    Returns:
        Dict with 'upper', 'middle', 'lower', and 'bandwidth'.

    Raises:
        ValueError: If insufficient data for calculation.
    """
    if len(prices) < period:
        raise ValueError(f"Insufficient data: need at least {period} prices")

    # Calculate middle band (SMA)
    middle = sum(prices[-period:]) / period

    # Calculate standard deviation
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


def calculate_kdj(prices_high: list, prices_low: list, prices_close: list, period: int = 9) -> dict:
    """Calculate KDJ (Stochastic) Indicator.

    Args:
        prices_high: List of historical high prices.
        prices_low: List of historical low prices.
        prices_close: List of historical closing prices.
        period: KDJ period (default 9).

    Returns:
        Dict with 'k', 'd', and 'j' values.

    Raises:
        ValueError: If insufficient data for calculation.
    """
    if len(prices_high) < period or len(prices_low) < period or len(prices_close) < period:
        raise ValueError(f"Insufficient data: need at least {period} prices")

    # Calculate RSV (Raw Stochastic Value)
    high_max = max(prices_high[-period:])
    low_min = min(prices_low[-period:])
    close = prices_close[-1]

    if high_max == low_min:
        rsv = 50.0
    else:
        rsv = (close - low_min) / (high_max - low_min) * 100

    # Calculate K, D, J (simplified version)
    k = rsv  # Using RSV as K for simplicity
    d = (k + 50) / 2  # Simplified D
    j = 3 * k - 2 * d

    return {
        "k": round(k, 2),
        "d": round(d, 2),
        "j": round(j, 2),
    }


def calculate_williams_r(prices_high: list, prices_low: list, prices_close: list, period: int = 14) -> dict:
    """Calculate Williams %R Indicator.

    Args:
        prices_high: List of historical high prices.
        prices_low: List of historical low prices.
        prices_close: List of historical closing prices.
        period: Williams %R period (default 14).

    Returns:
        Dict with 'williams_r' and 'signal'.

    Raises:
        ValueError: If insufficient data for calculation.
    """
    if len(prices_high) < period or len(prices_low) < period or len(prices_close) < period:
        raise ValueError(f"Insufficient data: need at least {period} prices")

    high_max = max(prices_high[-period:])
    low_min = min(prices_low[-period:])
    close = prices_close[-1]

    if high_max == low_min:
        williams_r = -50.0
    else:
        williams_r = (high_max - close) / (high_max - low_min) * -100

    # Signal: Overbought (> -20) or Oversold (< -80)
    if williams_r > -20:
        signal = "OVERBOUGHT"
    elif williams_r < -80:
        signal = "OVERSOLD"
    else:
        signal = "NEUTRAL"

    return {
        "williams_r": round(williams_r, 2),
        "signal": signal,
    }


def calculate_pivot_points(prices_high: float, prices_low: float, prices_close: float) -> dict:
    """Calculate Pivot Points and support/resistance levels.

    Args:
        prices_high: Previous period high price.
        prices_low: Previous period low price.
        prices_close: Previous period closing price.

    Returns:
        Dict with pivot point, support and resistance levels.

    Raises:
        ValueError: If prices are invalid.
    """
    if prices_high <= 0 or prices_low <= 0 or prices_close <= 0:
        raise ValueError("Invalid price data")

    pivot = (prices_high + prices_low + prices_close) / 3

    r1 = 2 * pivot - prices_low
    s1 = 2 * pivot - prices_high
    r2 = pivot + (prices_high - prices_low)
    s2 = pivot - (prices_high - prices_low)

    return {
        "pivot": round(pivot, 2),
        "r1": round(r1, 2),
        "r2": round(r2, 2),
        "s1": round(s1, 2),
        "s2": round(s2, 2),
    }


def calculate_all_indicators(
    prices: list,
    prices_high: list = None,
    prices_low: list = None,
    symbol: str = None
) -> dict:
    """Calculate all technical indicators.

    Args:
        prices: List of historical closing prices.
        prices_high: Optional list of historical high prices.
        prices_low: Optional list of historical low prices.
        symbol: Optional stock symbol for metadata.

    Returns:
        Dict with all indicators, symbol, and timestamp.
    """
    result = {
        "rsi": round(calculate_rsi(prices), 2),
        "macd": calculate_macd(prices),
        "ma": calculate_ma(prices, periods=[5, 10, 20, 60]),
        "bollinger_bands": calculate_bollinger_bands(prices),
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
    }

    # Add KDJ if high/low data available
    if prices_high and prices_low and len(prices_high) >= 9 and len(prices_low) >= 9:
        result["kdj"] = calculate_kdj(prices_high, prices_low, prices)

    # Add Williams %R if high/low data available
    if prices_high and prices_low and len(prices_high) >= 14 and len(prices_low) >= 14:
        result["williams_r"] = calculate_williams_r(prices_high, prices_low, prices)

    return result

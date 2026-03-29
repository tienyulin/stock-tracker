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


def calculate_all_indicators(prices: list, symbol: str = None) -> dict:
    """Calculate all technical indicators.

    Args:
        prices: List of historical prices.
        symbol: Optional stock symbol for metadata.

    Returns:
        Dict with RSI, MACD, MA, symbol, and timestamp.
    """
    result = {
        "rsi": round(calculate_rsi(prices), 2),
        "macd": calculate_macd(prices),
        "ma": calculate_ma(prices, periods=[5, 10, 20, 60]),
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
    }
    return result

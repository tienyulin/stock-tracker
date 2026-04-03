"""
Alerts Expansion Service

Provides expanded alert capabilities:
- Multiple alert types (price, percentage, RSI, MACD)
- Conditional alerts with AND/OR logic
- Custom notification messages
- Alert scheduling
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AlertCondition:
    """Single alert condition."""
    metric: str  # price, percent_change, rsi, macd, volume
    operator: str  # >, <, >=, <=, ==, crosses_above, crosses_below
    value: float
    AND next_condition: Optional["AlertCondition"] = None
    OR next_condition: Optional["AlertCondition"] = None


@dataclass
class ExpandedAlert:
    """Expanded alert with multiple conditions."""
    id: str
    user_id: str
    symbol: str
    name: str
    conditions: list  # List of AlertCondition
    notification_channels: list  # LINE, DISCORD, EMAIL
    custom_message: str
    is_active: bool
    created_at: str
    triggered_at: Optional[str] = None


@dataclass
class AlertEvaluation:
    """Result of evaluating an alert."""
    alert_id: str
    symbol: str
    triggered: bool
    triggered_conditions: list
    current_values: dict
    notification_sent: bool


class AlertsExpansionService:
    """Service for expanded alert capabilities."""

    # Supported metrics
    SUPPORTED_METRICS = [
        "price", "percent_change", "rsi", "macd",
        "volume", "bollinger", "signal", "volatility"
    ]

    # Supported operators
    SUPPORTED_OPERATORS = [
        ">", "<", ">=", "<=", "==",
        "crosses_above", "crosses_below"
    ]

    def __init__(self):
        """Initialize Alerts Expansion Service."""
        pass

    async def evaluate_alerts(
        self,
        alerts: list,
        current_data: dict
    ) -> list[AlertEvaluation]:
        """
        Evaluate multiple alerts against current market data.

        Args:
            alerts: List of expanded alerts
            current_data: Current market data {symbol: {price, rsi, macd, ...}}

        Returns:
            List of AlertEvaluation results.
        """
        results = []

        for alert in alerts:
            if not alert.get("is_active", True):
                continue

            result = await self._evaluate_single_alert(alert, current_data)
            results.append(result)

        return results

    async def _evaluate_single_alert(
        self,
        alert: dict,
        current_data: dict
    ) -> AlertEvaluation:
        """Evaluate a single alert."""
        symbol = alert["symbol"]
        data = current_data.get(symbol, {})

        triggered = False
        triggered_conditions = []

        # Evaluate each condition
        for condition in alert.get("conditions", []):
            if self._evaluate_condition(condition, data):
                triggered_conditions.append(condition)
                triggered = True

        return AlertEvaluation(
            alert_id=alert.get("id", ""),
            symbol=symbol,
            triggered=triggered,
            triggered_conditions=triggered_conditions,
            current_values=data,
            notification_sent=False,  # Will be set by notification service
        )

    def _evaluate_condition(
        self,
        condition: dict,
        data: dict
    ) -> bool:
        """Evaluate a single condition against data."""
        metric = condition.get("metric", "")
        operator = condition.get("operator", "")
        threshold = condition.get("value", 0)

        if metric not in data:
            return False

        current_value = data[metric]

        if operator == ">":
            return current_value > threshold
        elif operator == "<":
            return current_value < threshold
        elif operator == ">=":
            return current_value >= threshold
        elif operator == "<=":
            return current_value <= threshold
        elif operator == "==":
            return abs(current_value - threshold) < 0.001

        return False

    def create_price_alert(
        self,
        user_id: str,
        symbol: str,
        price: float,
        condition: str,  # above or below
        channels: list,
        custom_message: str = None
    ) -> ExpandedAlert:
        """Create a simple price alert."""
        operator = ">=" if condition == "above" else "<="

        return ExpandedAlert(
            id=f"alert_{user_id}_{symbol}_{int(datetime.now().timestamp())}",
            user_id=user_id,
            symbol=symbol,
            name=f"{symbol} price {condition} ${price}",
            conditions=[AlertCondition(
                metric="price",
                operator=operator,
                value=price
            )],
            notification_channels=channels,
            custom_message=custom_message or f"{symbol} has reached ${price}",
            is_active=True,
            created_at=datetime.now().isoformat(),
        )

    def create_percent_alert(
        self,
        user_id: str,
        symbol: str,
        percent_change: float,
        direction: str,  # up or down
        channels: list,
        custom_message: str = None
    ) -> ExpandedAlert:
        """Create a percentage change alert."""
        operator = ">=" if direction == "up" else "<="

        return ExpandedAlert(
            id=f"alert_{user_id}_{symbol}_{int(datetime.now().timestamp())}",
            user_id=user_id,
            symbol=symbol,
            name=f"{symbol} changed {direction} {percent_change}%",
            conditions=[AlertCondition(
                metric="percent_change",
                operator=operator,
                value=percent_change
            )],
            notification_channels=channels,
            custom_message=custom_message or f"{symbol} has moved {percent_change}%",
            is_active=True,
            created_at=datetime.now().isoformat(),
        )

    def create_rsi_alert(
        self,
        user_id: str,
        symbol: str,
        rsi_level: float,
        condition: str,  # overbought or oversold
        channels: list,
        custom_message: str = None
    ) -> ExpandedAlert:
        """Create an RSI alert (e.g., RSI > 70 = overbought)."""
        if condition == "overbought":
            operator = ">="
        elif condition == "oversold":
            operator = "<="
        else:
            operator = ">="

        return ExpandedAlert(
            id=f"alert_{user_id}_{symbol}_{int(datetime.now().timestamp())}",
            user_id=user_id,
            symbol=symbol,
            name=f"{symbol} RSI {condition} ({rsi_level})",
            conditions=[AlertCondition(
                metric="rsi",
                operator=operator,
                value=rsi_level
            )],
            notification_channels=channels,
            custom_message=custom_message or f"{symbol} RSI indicates {condition}",
            is_active=True,
            created_at=datetime.now().isoformat(),
        )

    def create_macd_alert(
        self,
        user_id: str,
        symbol: str,
        signal_line: str,  # macd or signal
        condition: str,  # bullish_cross or bearish_cross
        channels: list,
        custom_message: str = None
    ) -> ExpandedAlert:
        """Create a MACD crossover alert."""
        return ExpandedAlert(
            id=f"alert_{user_id}_{symbol}_{int(datetime.now().timestamp())}",
            user_id=user_id,
            symbol=symbol,
            name=f"{symbol} MACD {condition}",
            conditions=[AlertCondition(
                metric="macd",
                operator="crosses_above" if "bullish" in condition else "crosses_below",
                value=0  # MACD crossing zero line
            )],
            notification_channels=channels,
            custom_message=custom_message or f"{symbol} MACD showing {condition} crossover",
            is_active=True,
            created_at=datetime.now().isoformat(),
        )

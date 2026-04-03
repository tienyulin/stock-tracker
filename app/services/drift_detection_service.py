"""
Drift Detection Service

Detects when portfolio holdings drift away from AI Signal recommendations
and provides auto-rebalancing suggestions.
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class HoldingDrift:
    """Drift information for a single holding."""
    symbol: str
    current_quantity: float
    current_value: float
    current_weight: float  # Current portfolio weight
    recommended_signal: str  # BUY, SELL, HOLD, etc.
    recommended_weight: float  # Recommended portfolio weight
    drift_percentage: float  # |current_weight - recommended_weight|
    action: str  # BUY, SELL, HOLD
    action_quantity: float  # Shares to buy/sell to rebalance
    action_value: float  # Dollar value to buy/sell


@dataclass
class PortfolioDriftResult:
    """Complete drift analysis result."""
    total_value: float
    drift_score: float  # Overall drift score (0-100%)
    holdings: list[HoldingDrift]
    rebalancing_trades: list[HoldingDrift]  # Only non-zero actions
    rebalancing_total_buy: float  # Total buy value
    rebalancing_total_sell: float  # Total sell value
    timestamp: str


class DriftDetectionService:
    """Service for detecting portfolio drift from AI signals."""

    # Drift threshold to trigger alert (10% weight deviation)
    DRIFT_THRESHOLD = 0.10

    # Signals that indicate overweight
    OVERWEIGHT_SIGNALS = {"SELL", "STRONG_SELL"}

    # Signals that indicate underweight
    UNDERWEIGHT_SIGNALS = {"BUY", "STRONG_BUY"}

    def __init__(self):
        """Initialize Drift Detection Service."""
        pass

    async def calculate_drift(
        self,
        holdings: list[dict],
        prices: dict[str, float],
        signals: dict[str, dict],
        portfolio_value: float
    ) -> PortfolioDriftResult:
        """
        Calculate portfolio drift from signal recommendations.

        Args:
            holdings: List of holding dicts with 'symbol', 'quantity', 'avg_cost'
            prices: Current prices dict {symbol: price}
            signals: Signal recommendations {symbol: {'signal': 'BUY', 'confidence': 0.8}}
            portfolio_value: Total portfolio value

        Returns:
            PortfolioDriftResult with drift analysis and rebalancing suggestions.
        """
        if not holdings or portfolio_value == 0:
            return PortfolioDriftResult(
                total_value=0,
                drift_score=0,
                holdings=[],
                rebalancing_trades=[],
                rebalancing_total_buy=0,
                rebalancing_total_sell=0,
                timestamp="",
            )

        holding_drifts = []
        total_drift = 0.0

        for h in holdings:
            symbol = h["symbol"]
            current_price = prices.get(symbol, 0)
            current_value = h["quantity"] * current_price
            current_weight = current_value / portfolio_value

            # Get recommended signal
            signal_info = signals.get(symbol, {})
            recommended_signal = signal_info.get("signal", "HOLD")

            # Calculate recommended weight based on signal
            recommended_weight = self._get_recommended_weight(
                recommended_signal,
                signal_info.get("confidence", 0.5),
                len(holdings)
            )

            # Calculate drift
            drift_percentage = abs(current_weight - recommended_weight)
            total_drift += drift_percentage

            # Determine action
            action, action_quantity, action_value = self._calculate_rebalance_action(
                current_weight=current_weight,
                recommended_weight=recommended_weight,
                current_price=current_price,
                portfolio_value=portfolio_value,
                recommended_signal=recommended_signal,
            )

            holding_drifts.append(HoldingDrift(
                symbol=symbol,
                current_quantity=h["quantity"],
                current_value=current_value,
                current_weight=current_weight,
                recommended_signal=recommended_signal,
                recommended_weight=recommended_weight,
                drift_percentage=drift_percentage,
                action=action,
                action_quantity=action_quantity,
                action_value=action_value,
            ))

        # Filter to only rebalancing trades (non-zero actions)
        rebalancing_trades = [h for h in holding_drifts if h.action != "HOLD"]
        total_buy = sum(h.action_value for h in rebalancing_trades if h.action == "BUY")
        total_sell = sum(h.action_value for h in rebalancing_trades if h.action == "SELL")

        # Drift score: normalize total drift to 0-100 scale
        # Max possible drift is 2.0 (100% overweight vs 100% underweight)
        drift_score = min(100.0, (total_drift / 2.0) * 100)

        from datetime import datetime
        return PortfolioDriftResult(
            total_value=portfolio_value,
            drift_score=round(drift_score, 2),
            holdings=holding_drifts,
            rebalancing_trades=rebalancing_trades,
            rebalancing_total_buy=round(total_buy, 2),
            rebalancing_total_sell=round(total_sell, 2),
            timestamp=datetime.now().isoformat(),
        )

    def _get_recommended_weight(
        self,
        signal: str,
        confidence: float,
        num_holdings: int
    ) -> float:
        """
        Calculate recommended portfolio weight based on signal.

        Args:
            signal: Signal type (BUY, SELL, HOLD, etc.)
            confidence: Signal confidence (0-1)
            num_holdings: Number of holdings in portfolio

        Returns:
            Recommended portfolio weight (0-1).
        """
        # Base weight (equal distribution)
        base_weight = 1.0 / num_holdings

        if signal == "STRONG_BUY":
            return min(1.0, base_weight * (1.0 + confidence))
        elif signal == "BUY":
            return min(1.0, base_weight * (1.0 + confidence * 0.5))
        elif signal == "STRONG_SELL":
            return max(0.0, base_weight * (1.0 - confidence))
        elif signal == "SELL":
            return max(0.0, base_weight * (1.0 - confidence * 0.5))
        else:  # HOLD
            return base_weight

    def _calculate_rebalance_action(
        self,
        current_weight: float,
        recommended_weight: float,
        current_price: float,
        portfolio_value: float,
        recommended_signal: str
    ) -> tuple[str, float, float]:
        """
        Calculate rebalancing action for a holding.

        Returns:
            Tuple of (action, quantity, value).
        """
        drift = recommended_weight - current_weight
        drift_value = drift * portfolio_value

        if abs(drift) < self.DRIFT_THRESHOLD:
            return "HOLD", 0, 0

        if current_price <= 0:
            return "HOLD", 0, 0

        quantity = abs(drift_value) / current_price

        if recommended_signal in self.OVERWEIGHT_SIGNALS:
            # Need to sell
            return "SELL", quantity, abs(drift_value)
        elif recommended_signal in self.UNDERWEIGHT_SIGNALS:
            # Need to buy
            return "BUY", quantity, abs(drift_value)
        else:
            return "HOLD", 0, 0

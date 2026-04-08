"""
Drift Detection Service

Detects when portfolio holdings drift away from AI Signal recommendations
and provides auto-rebalancing suggestions.
"""
from __future__ import annotations

from dataclasses import dataclass


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
class AutoRebalanceTrigger:
    """Auto-rebalancing trigger decision."""
    should_rebalance: bool
    reason: str
    triggered_by: str  # "drift_threshold", "manual", "scheduled"
    drift_threshold: float  # Threshold that triggered
    max_single_drift: float  # Max individual holding drift
    overall_drift_score: float  # Portfolio-level drift score
    priority: str  # LOW, MEDIUM, HIGH
    estimated_trade_count: int
    estimated_tax_impact: float  # Estimated tax from rebalancing trades


@dataclass
class RebalanceOrder:
    """Single rebalancing trade order."""
    symbol: str
    action: str  # BUY or SELL
    quantity: float
    estimated_price: float
    estimated_value: float
    reason: str  # e.g., "drift 12.3% exceeds threshold 10%"
    urgency: str  # LOW, MEDIUM, HIGH
    tax_loss_harvesting_eligible: bool = False
    wash_sale_risk: bool = False


@dataclass
class PortfolioDriftResult:
    """Complete drift analysis result."""
    total_value: float
    drift_score: float  # Overall drift score (0-100%)
    holdings: list[HoldingDrift]
    rebalancing_trades: list[HoldingDrift]  # Only non-zero actions
    rebalancing_total_buy: float  # Total buy value
    rebalancing_total_sell: float  # Total sell value
    auto_rebalance_trigger: "AutoRebalanceTrigger" = None  # Phase 30: Auto-rebalance
    rebalance_orders: list[RebalanceOrder] = None  # Phase 30: Executable orders
    timestamp: str = ""


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

    # ─── Phase 30: Auto-Rebalancing ───────────────────────────────────────

    def check_auto_rebalance_trigger(
        self,
        drift_result: PortfolioDriftResult,
        min_trades: int = 1,
        max_tax_impact: float = 5000.0,
        user_risk_tolerance: str = "MEDIUM",
    ) -> AutoRebalanceTrigger:
        """
        Check if auto-rebalancing should be triggered.

        Phase 30 enhancement: Automatically determines if rebalancing
        should be triggered based on drift thresholds.

        Args:
            drift_result: The drift analysis result
            min_trades: Minimum number of rebalancing trades to trigger
            max_tax_impact: Maximum acceptable tax impact from rebalancing
            user_risk_tolerance: User's risk tolerance (LOW, MEDIUM, HIGH)

        Returns:
            AutoRebalanceTrigger with decision and metadata.
        """
        if drift_result.drift_score == 0:
            return AutoRebalanceTrigger(
                should_rebalance=False,
                reason="No drift detected",
                triggered_by="none",
                drift_threshold=self.DRIFT_THRESHOLD,
                max_single_drift=0,
                overall_drift_score=0,
                priority="NONE",
                estimated_trade_count=0,
                estimated_tax_impact=0,
            )

        # Check individual holding drifts
        max_drift = max((h.drift_percentage for h in drift_result.holdings), default=0)

        # Check trade count
        trade_count = len(drift_result.rebalancing_trades)
        if trade_count < min_trades:
            return AutoRebalanceTrigger(
                should_rebalance=False,
                reason=f"Insufficient rebalancing trades ({trade_count} < {min_trades})",
                triggered_by="none",
                drift_threshold=self.DRIFT_THRESHOLD,
                max_single_drift=max_drift,
                overall_drift_score=drift_result.drift_score,
                priority="NONE",
                estimated_trade_count=trade_count,
                estimated_tax_impact=0,
            )

        # Determine if any individual holding exceeds drift threshold
        triggered_by = "drift_threshold"
        reason = ""
        priority = "LOW"
        should_rebalance = False

        if max_drift > self.DRIFT_THRESHOLD:
            should_rebalance = True

            if max_drift > 0.20:
                priority = "HIGH"
                reason = f"Critical drift: {max_drift:.1%} exceeds 20% (highest threshold)"
            elif max_drift > 0.15:
                priority = "HIGH" if user_risk_tolerance == "LOW" else "MEDIUM"
                reason = f"High drift: {max_drift:.1%} exceeds 15%"
            elif max_drift > self.DRIFT_THRESHOLD:
                priority = "MEDIUM" if user_risk_tolerance == "LOW" else "LOW"
                reason = f"Drift {max_drift:.1%} exceeds threshold {self.DRIFT_THRESHOLD:.0%}"

            triggered_by = "drift_threshold"

        # Check portfolio-level drift score
        if drift_result.drift_score > 30:
            should_rebalance = True
            triggered_by = "drift_score"
            reason = f"Portfolio drift score {drift_result.drift_score:.1f}% is very high"
            if priority not in ("HIGH",):
                priority = "MEDIUM"

        # Apply risk tolerance adjustment
        if user_risk_tolerance == "LOW" and max_drift > 0.05:
            should_rebalance = True
            reason = f"Conservative threshold: {max_drift:.1%} exceeds 5%"
            triggered_by = "risk_tolerance"

        # Estimate tax impact (simplified: assume 20% cap gains on sell trades)
        estimated_sells = sum(
            h.action_value for h in drift_result.rebalancing_trades
            if h.action == "SELL"
        )
        estimated_tax = estimated_sells * 0.20 * 0.3  # 20% rate × 30% gain probability

        if estimated_tax > max_tax_impact and user_risk_tolerance != "HIGH":
            should_rebalance = False
            reason += f" | Tax impact ${estimated_tax:.0f} exceeds max ${max_tax_impact:.0f}"

        return AutoRebalanceTrigger(
            should_rebalance=should_rebalance,
            reason=reason or "Drift within acceptable range",
            triggered_by=triggered_by,
            drift_threshold=self.DRIFT_THRESHOLD,
            max_single_drift=round(max_drift, 4),
            overall_drift_score=drift_result.drift_score,
            priority=priority,
            estimated_trade_count=trade_count,
            estimated_tax_impact=round(estimated_tax, 2),
        )

    def generate_rebalance_orders(
        self,
        drift_result: PortfolioDriftResult,
        prices: dict[str, float],
        purchase_dates: dict[str, str] = None,
        urgency: str = "MEDIUM",
    ) -> list[RebalanceOrder]:
        """
        Generate executable rebalancing orders from drift analysis.

        Phase 30 enhancement: Converts drift analysis into
        concrete, actionable trade orders.

        Args:
            drift_result: The drift analysis result
            prices: Current prices {symbol: price}
            purchase_dates: Optional {symbol: purchase_date} for tax analysis
            urgency: Overall order urgency (LOW, MEDIUM, HIGH)

        Returns:
            List of RebalanceOrder to execute.
        """
        if drift_result is None or not drift_result.rebalancing_trades:
            return []

        orders = []
        for trade in drift_result.rebalancing_trades:
            current_price = prices.get(trade.symbol, 0)
            if current_price <= 0:
                current_price = trade.current_value / trade.current_quantity if trade.current_quantity > 0 else 0

            # Assess tax-loss harvesting eligibility
            harvest_eligible = False
            wash_sale_risk = False

            if purchase_dates and trade.action == "SELL":
                pdate = purchase_dates.get(trade.symbol)
                if pdate:
                    try:
                        from datetime import datetime
                        purchase = datetime.strptime(pdate, "%Y-%m-%d")
                        days_held = (datetime.now() - purchase).days
                        # Eligible if held > 30 days (long-term)
                        harvest_eligible = days_held > 30
                        wash_sale_risk = days_held < 61
                    except (ValueError, TypeError):
                        pass

            # Determine per-order urgency based on drift
            drift_pct = trade.drift_percentage
            if drift_pct > 0.20:
                order_urgency = "HIGH"
            elif drift_pct > 0.15:
                order_urgency = "MEDIUM"
            else:
                order_urgency = urgency

            orders.append(RebalanceOrder(
                symbol=trade.symbol,
                action=trade.action,
                quantity=round(trade.action_quantity, 4),
                estimated_price=current_price,
                estimated_value=round(trade.action_value, 2),
                reason=f"drift {drift_pct:.1%} exceeds threshold {self.DRIFT_THRESHOLD:.0%}",
                urgency=order_urgency,
                tax_loss_harvesting_eligible=harvest_eligible,
                wash_sale_risk=wash_sale_risk,
            ))

        return orders

    async def calculate_drift_with_auto_rebalance(
        self,
        holdings: list[dict],
        prices: dict[str, float],
        signals: dict[str, dict],
        portfolio_value: float,
        purchase_dates: dict[str, str] = None,
        auto_rebalance: bool = True,
        user_risk_tolerance: str = "MEDIUM",
    ) -> PortfolioDriftResult:
        """
        Phase 30 enhanced drift calculation with auto-rebalancing support.

        This is the main entry point for Phase 30 features. It runs the
        standard drift calculation and optionally generates auto-rebalance
        orders when drift exceeds thresholds.

        Args:
            holdings: List of holding dicts
            prices: Current prices dict
            signals: Signal recommendations
            portfolio_value: Total portfolio value
            purchase_dates: Optional {symbol: purchase_date} for tax analysis
            auto_rebalance: Whether to generate rebalance orders
            user_risk_tolerance: User's risk tolerance (LOW, MEDIUM, HIGH)

        Returns:
            PortfolioDriftResult with auto-rebalance data populated.
        """
        # Run standard drift calculation
        result = await self.calculate_drift(
            holdings=holdings,
            prices=prices,
            signals=signals,
            portfolio_value=portfolio_value,
        )

        if not auto_rebalance:
            return result

        # Check auto-rebalance trigger
        trigger = self.check_auto_rebalance_trigger(
            drift_result=result,
            user_risk_tolerance=user_risk_tolerance,
        )

        # Generate orders if triggered
        orders = []
        if trigger.should_rebalance:
            orders = self.generate_rebalance_orders(
                drift_result=result,
                prices=prices,
                purchase_dates=purchase_dates,
            )

        # Attach Phase 30 data
        result.auto_rebalance_trigger = trigger
        result.rebalance_orders = orders

        return result

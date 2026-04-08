"""
Tax-Loss Harvesting Service

Identifies opportunities to harvest tax losses by selling positions
with unrealized losses, while avoiding wash sale rule violations.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TaxLot:
    """Individual tax lot for a position."""
    purchase_date: str
    quantity: float
    avg_cost: float
    current_price: float
    unrealized_gain: float
    unrealized_gain_percent: float
    days_held: int


@dataclass
class HarvestingCandidate:
    """Position identified as a tax-loss harvesting candidate."""
    symbol: str
    quantity: float
    current_price: float
    avg_cost: float
    unrealized_loss: float
    unrealized_loss_percent: float
    estimated_tax_savings: float  # Tax savings at capital gains rate
    wash_sale_risk: str  # LOW, MEDIUM, HIGH
    replacement_candidate: Optional[str]  # Similar stock to buy after wash sale
    action: str  # HARVEST, HOLD, SKIP
    # Phase 30: Enhanced fields
    days_held: int = 0
    holding_period_status: str = "SHORT"  # SHORT (<30), MEDIUM (30-60), LONG (>60)
    automated_eligible: bool = False  # Phase 30: Meets automated detection criteria
    automated_reason: Optional[str] = None


@dataclass
class TaxLossHarvestingResult:
    """Complete tax-loss harvesting analysis result."""
    total_unrealized_loss: float
    total_estimated_tax_savings: float
    candidates: list[HarvestingCandidate]
    harvesting_trades: list[HarvestingCandidate]  # Only HARVEST actions
    total_harvest_value: float
    replacement_suggestions: list[dict]  # Stocks to buy after selling
    capital_gains_rate: float
    timestamp: str
    # Phase 30: Automated detection
    automated_candidates: list[HarvestingCandidate] = None  # Auto-detected eligible
    automated_opportunities: list[dict] = None  # Ready-to-execute opportunities
    next_review_date: Optional[str] = None  # When to next check


class TaxLossHarvestingService:
    """Service for identifying and executing tax-loss harvesting opportunities."""

    # Wash sale rule: can't claim loss if you buy substantially identical
    # security within 30 days before or after the sale
    WASH_SALE_WINDOW_DAYS = 30

    # Minimum loss threshold to consider harvesting ($100)
    MIN_LOSS_THRESHOLD = 100.0

    # Minimum loss percent to consider harvesting (5%)
    MIN_LOSS_PERCENT = 0.05

    # Tax rates (simplified - could be from user profile)
    SHORT_TERM_CAPITAL_GAINS_RATE = 0.37  # 37% for income > ~$500k
    LONG_TERM_CAPITAL_GAINS_RATE = 0.20  # 20% for long-term

    # Similar stocks to suggest as replacements (to avoid wash sales)
    REPLACEMENT_CANDIDATES = {
        "AAPL": ["MSFT", "GOOGL"],
        "GOOGL": ["MSFT", "AAPL"],
        "MSFT": ["AAPL", "GOOGL"],
        "AMZN": ["WMT", "TGT"],
        "TSLA": ["F", "GM"],
        "NVDA": ["AMD", "INTC"],
        "META": ["SNAP", "PINS"],
        "SPY": ["VOO", "IVV"],
        "QQQ": ["QQQM", "VGT"],
        "^GSPC": ["VOO", "IVV"],
    }

    def __init__(self, short_term_rate: float = None, long_term_rate: float = None):
        """Initialize Tax-Loss Harvesting Service."""
        self.short_term_rate = short_term_rate or self.SHORT_TERM_CAPITAL_GAINS_RATE
        self.long_term_rate = long_term_rate or self.LONG_TERM_CAPITAL_GAINS_RATE

    def calculate_harvesting_opportunities(
        self,
        holdings: list[dict],
        prices: dict[str, float],
        purchase_dates: dict[str, str] = None,  # {symbol: purchase_date}
        risk_tolerance: str = "MEDIUM",  # LOW, MEDIUM, HIGH
    ) -> TaxLossHarvestingResult:
        """
        Analyze portfolio for tax-loss harvesting opportunities.

        Args:
            holdings: List of holding dicts with 'symbol', 'quantity', 'avg_cost'
            prices: Current prices dict {symbol: price}
            purchase_dates: Optional dict of purchase dates {symbol: date_string}
            risk_tolerance: User's risk tolerance (affects wash sale warnings)

        Returns:
            TaxLossHarvestingResult with harvesting opportunities and suggestions.
        """
        candidates = []
        total_unrealized_loss = 0.0
        total_estimated_tax_savings = 0.0
        replacement_suggestions = set()

        for h in holdings:
            symbol = h["symbol"]
            quantity = h["quantity"]
            avg_cost = h["avg_cost"]
            current_price = prices.get(symbol, 0)

            if current_price <= 0 or quantity <= 0:
                continue

            current_value = current_price * quantity
            cost_basis = avg_cost * quantity
            unrealized_gain = current_value - cost_basis
            unrealized_gain_percent = unrealized_gain / cost_basis if cost_basis > 0 else 0

            # Only consider positions with losses
            if unrealized_gain >= 0:
                continue

            unrealized_loss = abs(unrealized_gain)
            loss_percent = abs(unrealized_gain_percent)

            # Apply thresholds
            if unrealized_loss < self.MIN_LOSS_THRESHOLD:
                continue
            if loss_percent < self.MIN_LOSS_PERCENT:
                continue

            # Calculate estimated tax savings
            is_long_term = True  # Assume long-term unless we know otherwise
            if is_long_term:
                tax_rate = self.long_term_rate
            else:
                tax_rate = self.short_term_rate

            estimated_tax_savings = unrealized_loss * tax_rate

            # Determine wash sale risk
            purchase_date = purchase_dates.get(symbol) if purchase_dates else None
            wash_sale_risk = self._assess_wash_sale_risk(symbol, purchase_date, risk_tolerance)

            # Get replacement candidate
            replacement = self._get_replacement_candidate(symbol)

            # Determine action
            if wash_sale_risk == "HIGH" and risk_tolerance == "LOW":
                action = "SKIP"
            elif wash_sale_risk == "HIGH":
                action = "HOLD"
            else:
                action = "HARVEST"
                total_unrealized_loss += unrealized_loss
                total_estimated_tax_savings += estimated_tax_savings
                if replacement:
                    replacement_suggestions.add(replacement)

            candidates.append(HarvestingCandidate(
                symbol=symbol,
                quantity=quantity,
                current_price=current_price,
                avg_cost=avg_cost,
                unrealized_loss=unrealized_loss,
                unrealized_loss_percent=loss_percent,
                estimated_tax_savings=estimated_tax_savings,
                wash_sale_risk=wash_sale_risk,
                replacement_candidate=replacement,
                action=action,
            ))

        # Filter to harvesting trades only
        harvesting_trades = [c for c in candidates if c.action == "HARVEST"]
        total_harvest_value = sum(c.unrealized_loss for c in harvesting_trades)

        return TaxLossHarvestingResult(
            total_unrealized_loss=round(total_unrealized_loss, 2),
            total_estimated_tax_savings=round(total_estimated_tax_savings, 2),
            candidates=candidates,
            harvesting_trades=harvesting_trades,
            total_harvest_value=round(total_harvest_value, 2),
            replacement_suggestions=[
                {"symbol": s, "reason": "Substitute to maintain market exposure after harvesting"}
                for s in replacement_suggestions
            ],
            capital_gains_rate=self.long_term_rate,
            timestamp=datetime.now().isoformat(),
        )

    def _assess_wash_sale_risk(
        self,
        symbol: str,
        purchase_date: str,
        risk_tolerance: str
    ) -> str:
        """
        Assess the wash sale rule risk for a potential harvest.

        Returns:
            Risk level: LOW, MEDIUM, or HIGH
        """
        if not purchase_date:
            # Unknown purchase date means we can't assess properly
            return "MEDIUM"

        try:
            purchase = datetime.strptime(purchase_date, "%Y-%m-%d")
            days_held = (datetime.now() - purchase).days

            # If held less than 31 days, high risk of wash sale
            if days_held < 31:
                return "HIGH"
            elif days_held < 61:
                return "MEDIUM"
            else:
                return "LOW"
        except (ValueError, TypeError):
            return "MEDIUM"

    def _get_replacement_candidate(self, symbol: str) -> Optional[str]:
        """
        Get a similar stock to use as replacement after harvest.

        This helps maintain market exposure while avoiding wash sale rules.
        """
        # Check if it's an ETF or index
        if symbol in self.REPLACEMENT_CANDIDATES:
            candidates = self.REPLACEMENT_CANDIDATES[symbol]
            return candidates[0] if candidates else None

        # For individual stocks, suggest sector ETF
        sector_etfs = {
            "AAPL": "XLK", "MSFT": "XLK", "GOOGL": "XLK", "AMZN": "XLY",
            "TSLA": "XLY", "NVDA": "SMH", "AMD": "SMH", "META": "XLC",
        }

        return sector_etfs.get(symbol)

    # ─── Phase 30: Automated Opportunity Detection ─────────────────────────

    # Thresholds for automated detection
    AUTOMATED_MIN_LOSS = 1000.0  # Minimum loss for automated detection
    AUTOMATED_MIN_DAYS = 30  # Minimum holding period for automated
    AUTOMATED_MIN_LOSS_PERCENT = 0.05  # Minimum 5% loss

    def detect_automated_opportunities(
        self,
        holdings: list[dict],
        prices: dict[str, float],
        purchase_dates: dict[str, str] = None,
    ) -> list[HarvestingCandidate]:
        """
        Phase 30: Automated tax-loss harvesting opportunity detection.

        Identifies positions that meet BOTH criteria:
        1. Holding period > 30 days (avoids wash sale risk)
        2. Unrealized loss > $1000 AND > 5% of cost basis

        These candidates are flagged as `automated_eligible=True`
        and can be auto-harvested with appropriate safeguards.

        Args:
            holdings: List of holding dicts
            prices: Current prices dict
            purchase_dates: Optional {symbol: purchase_date}

        Returns:
            List of HarvestingCandidate that are automated-eligible.
        """
        candidates = []

        for h in holdings:
            symbol = h["symbol"]
            quantity = h["quantity"]
            avg_cost = h["avg_cost"]
            current_price = prices.get(symbol, 0)

            if current_price <= 0 or quantity <= 0:
                continue

            current_value = current_price * quantity
            cost_basis = avg_cost * quantity
            unrealized_gain = current_value - cost_basis

            # Skip positions with gains
            if unrealized_gain >= 0:
                continue

            unrealized_loss = abs(unrealized_gain)
            loss_percent = unrealized_loss / cost_basis if cost_basis > 0 else 0

            # Check if meets automated thresholds
            if unrealized_loss < self.AUTOMATED_MIN_LOSS:
                continue
            if loss_percent < self.AUTOMATED_MIN_LOSS_PERCENT:
                continue

            # Check holding period
            purchase_date = purchase_dates.get(symbol) if purchase_dates else None
            days_held = 0
            holding_status = "SHORT"

            if purchase_date:
                try:
                    purchase = datetime.strptime(purchase_date, "%Y-%m-%d")
                    days_held = (datetime.now() - purchase).days
                    if days_held > 60:
                        holding_status = "LONG"
                    elif days_held >= 30:
                        holding_status = "MEDIUM"
                    else:
                        holding_status = "SHORT"
                except (ValueError, TypeError):
                    days_held = 0

            # Must meet minimum holding period
            if days_held < self.AUTOMATED_MIN_DAYS:
                continue

            # Assess wash sale risk
            if days_held < 61:
                wash_sale_risk = "HIGH"
            elif days_held < 91:
                wash_sale_risk = "MEDIUM"
            else:
                wash_sale_risk = "LOW"

            # Determine automated eligibility
            automated_eligible = (
                days_held >= self.AUTOMATED_MIN_DAYS
                and unrealized_loss >= self.AUTOMATED_MIN_LOSS
                and wash_sale_risk in ("LOW", "MEDIUM")
            )

            # Tax savings estimate
            tax_rate = self.long_term_rate if days_held >= 365 else self.short_term_rate
            estimated_tax_savings = unrealized_loss * tax_rate

            # Replacement candidate
            replacement = self._get_replacement_candidate(symbol)

            reason = None
            if automated_eligible:
                if wash_sale_risk == "LOW":
                    reason = f"Auto-eligible: {days_held} days held, loss ${unrealized_loss:,.0f}, wash sale risk LOW"
                else:
                    reason = f"Semi-eligible: {days_held} days held, loss ${unrealized_loss:,.0f}, wash sale risk {wash_sale_risk}"

            candidates.append(HarvestingCandidate(
                symbol=symbol,
                quantity=quantity,
                current_price=current_price,
                avg_cost=avg_cost,
                unrealized_loss=unrealized_loss,
                unrealized_loss_percent=loss_percent,
                estimated_tax_savings=round(estimated_tax_savings, 2),
                wash_sale_risk=wash_sale_risk,
                replacement_candidate=replacement,
                action="HARVEST" if automated_eligible else "HOLD",
                days_held=days_held,
                holding_period_status=holding_status,
                automated_eligible=automated_eligible,
                automated_reason=reason,
            ))

        # Sort by loss amount (largest first)
        candidates.sort(key=lambda c: c.unrealized_loss, reverse=True)
        return candidates

    def calculate_harvesting_opportunities_automated(
        self,
        holdings: list[dict],
        prices: dict[str, float],
        purchase_dates: dict[str, str] = None,
        risk_tolerance: str = "MEDIUM",
        auto_execute: bool = False,
    ) -> TaxLossHarvestingResult:
        """
        Phase 30: Enhanced tax-loss harvesting with automated detection.

        Main entry point for Phase 30. Runs both standard analysis and
        automated opportunity detection.

        Args:
            holdings: List of holding dicts
            prices: Current prices dict
            purchase_dates: Optional {symbol: purchase_date}
            risk_tolerance: User's risk tolerance (LOW, MEDIUM, HIGH)
            auto_execute: If True, also returns ready-to-execute opportunities

        Returns:
            TaxLossHarvestingResult with automated detection data.
        """
        # Run standard analysis
        result = self.calculate_harvesting_opportunities(
            holdings=holdings,
            prices=prices,
            purchase_dates=purchase_dates,
            risk_tolerance=risk_tolerance,
        )

        # Run automated detection
        automated_candidates = self.detect_automated_opportunities(
            holdings=holdings,
            prices=prices,
            purchase_dates=purchase_dates,
        )

        # Filter to fully automated-eligible (low wash sale risk)
        ready_to_execute = [
            c for c in automated_candidates
            if c.automated_eligible and c.wash_sale_risk == "LOW"
        ]

        # Build opportunity summaries
        automated_opportunities = []
        for c in ready_to_execute:
            automated_opportunities.append({
                "symbol": c.symbol,
                "unrealized_loss": round(c.unrealized_loss, 2),
                "estimated_tax_savings": c.estimated_tax_savings,
                "days_held": c.days_held,
                "replacement": c.replacement_candidate,
                "action": "SELL",
                "quantity": c.quantity,
                "estimated_value": c.unrealized_loss,
                "urgency": "HIGH" if c.unrealized_loss > 5000 else "MEDIUM",
                "note": c.automated_reason,
            })

        # Calculate next review date (when new opportunities may arise)
        from datetime import timedelta
        next_review = datetime.now() + timedelta(days=7)
        next_review_date = next_review.strftime("%Y-%m-%d")

        result.automated_candidates = automated_candidates
        result.automated_opportunities = automated_opportunities
        result.next_review_date = next_review_date

        return result

    def get_harvesting_calendar(
        self,
        holdings: list[dict],
        prices: dict[str, float],
        purchase_dates: dict[str, str],
        lookahead_days: int = 90,
    ) -> list[dict]:
        """
        Phase 30: Generate a harvesting calendar for upcoming opportunities.

        Identifies positions that will become eligible for automated
        harvesting in the next N days.

        Args:
            holdings: List of holding dicts
            prices: Current prices dict
            purchase_dates: {symbol: purchase_date}
            lookahead_days: Days to look ahead (default 90)

        Returns:
            List of upcoming harvesting opportunities with eligibility dates.
        """
        calendar = []
        now = datetime.now()

        for h in holdings:
            symbol = h["symbol"]
            quantity = h["quantity"]
            avg_cost = h["avg_cost"]
            current_price = prices.get(symbol, 0)

            if current_price <= 0 or quantity <= 0:
                continue

            current_value = current_price * quantity
            cost_basis = avg_cost * quantity
            unrealized_gain = current_value - cost_basis

            if unrealized_gain >= 0:
                continue

            unrealized_loss = abs(unrealized_gain)
            if unrealized_loss < self.AUTOMATED_MIN_LOSS:
                continue

            purchase_date_str = purchase_dates.get(symbol)
            if not purchase_date_str:
                continue

            try:
                purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d")
                days_held = (now - purchase_date).days

                if days_held >= 30:
                    # Already eligible
                    eligible_date = purchase_date + timedelta(days=30)
                    status = "ELIGIBLE_NOW"
                else:
                    # Will become eligible
                    days_until_eligible = 30 - days_held
                    if days_until_eligible <= lookahead_days:
                        eligible_date = now + timedelta(days=days_until_eligible)
                        status = f"ELIGIBLE_IN_{days_until_eligible}_DAYS"
                    else:
                        continue

                calendar.append({
                    "symbol": symbol,
                    "status": status,
                    "purchase_date": purchase_date_str,
                    "eligible_date": eligible_date.strftime("%Y-%m-%d"),
                    "days_held": days_held,
                    "days_until_eligible": max(0, 30 - days_held),
                    "unrealized_loss": round(unrealized_loss, 2),
                    "current_price": current_price,
                    "quantity": quantity,
                    "note": f"Will be eligible for automated harvesting on {eligible_date.strftime('%Y-%m-%d')}",
                })

            except (ValueError, TypeError):
                continue

        # Sort by eligible date
        calendar.sort(key=lambda x: x["eligible_date"])
        return calendar

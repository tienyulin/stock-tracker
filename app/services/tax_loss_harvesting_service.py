"""
Tax-Loss Harvesting Service

Identifies opportunities to harvest tax losses by selling positions
with unrealized losses, while avoiding wash sale rule violations.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
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

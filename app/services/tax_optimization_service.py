"""
Tax Optimization Service.

Provides tax optimization strategies and recommendations:
- Loss harvesting opportunity identification
- High turnover position warnings
- Holding period optimization
- Tax-efficient asset suggestions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class OptimizationType(Enum):
    """Types of tax optimization opportunities."""
    LOSS_HARVEST = "loss_harvest"
    GAIN_DEFER = "gain_defer"
    HOLDING_PERIOD = "holding_period"
    TURNOVER_WARNING = "turnover_warning"


class AssetTaxEfficiency(Enum):
    """Tax efficiency rating for asset types."""
    HIGH = "high"        # Growth ETFs, individual stocks
    MEDIUM = "medium"    # Balanced ETFs, REITs
    LOW = "low"          # High-yield bonds, actively managed funds


@dataclass
class TaxOptimizationOpportunity:
    """A single tax optimization opportunity."""
    type: OptimizationType
    symbol: str
    description: str
    action: str
    estimated_tax_savings: float  # USD
    urgency: str = "medium"  # low, medium, high
    details: dict = field(default_factory=dict)


@dataclass
class HoldingPeriodRecommendation:
    """Recommendation for optimizing holding period."""
    symbol: str
    current_holding_days: int
    days_to_long_term: int
    projected_gain_if_hold: float
    projected_gain_if_sell_now: float
    should_hold_until: Optional[datetime] = None


@dataclass
class PortfolioTaxSummary:
    """Tax summary for the entire portfolio."""
    total_unrealized_gains: float = 0.0
    total_unrealized_losses: float = 0.0
    short_term_unrealized_gains: float = 0.0
    short_term_unrealized_losses: float = 0.0
    long_term_unrealized_gains: float = 0.0
    long_term_unrealized_losses: float = 0.0
    net_unrealized: float = 0.0
    harvestable_losses: float = 0.0  # Losses that can offset gains
    expiring_this_year: float = 0.0  # Wash sale carryforwards
    opportunities: list[TaxOptimizationOpportunity] = field(default_factory=list)


class TaxOptimizationService:
    """Service for analyzing and optimizing portfolio taxes."""

    # IRS holding period threshold
    LONG_TERM_DAYS = 365

    # Wash sale window
    WASH_SALE_WINDOW = 30

    # Tax brackets (2024 short-term = ordinary income rates)
    SHORT_TERM_RATES = [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]

    # Long-term capital gains rates
    LONG_TERM_RATES = [0.00, 0.15, 0.20]

    def __init__(self, short_term_rate: float = 0.24, long_term_rate: float = 0.15):
        """
        Initialize Tax Optimization Service.

        Args:
            short_term_rate: User's marginal short-term (ordinary income) tax rate
            long_term_rate: User's long-term capital gains rate
        """
        self.short_term_rate = short_term_rate
        self.long_term_rate = long_term_rate

    def analyze_portfolio_tax(
        self,
        positions: list[dict],
        current_date: Optional[datetime] = None
    ) -> PortfolioTaxSummary:
        """
        Analyze all positions and generate tax optimization summary.

        Args:
            positions: List of position dicts with keys:
                - symbol: str
                - quantity: float
                - cost_basis: float
                - current_price: float
                - purchase_date: datetime
            current_date: Analysis date (default: now)

        Returns:
            PortfolioTaxSummary with all analysis
        """
        current_date = current_date or datetime.now()
        summary = PortfolioTaxSummary()

        for pos in positions:
            symbol = pos["symbol"]
            quantity = pos["quantity"]
            cost_basis = pos["cost_basis"]
            current_price = pos["current_price"]
            purchase_date = pos["purchase_date"]

            total_cost = cost_basis * quantity
            current_value = current_price * quantity
            unrealized = current_value - total_cost

            days_held = (current_date - purchase_date).days
            is_long_term = days_held >= self.LONG_TERM_DAYS

            if unrealized > 0:
                summary.total_unrealized_gains += unrealized
                if is_long_term:
                    summary.long_term_unrealized_gains += unrealized
                else:
                    summary.short_term_unrealized_gains += unrealized

                # Large unrealized gains in short-term
                if not is_long_term and unrealized > 5000:
                    opp = TaxOptimizationOpportunity(
                        type=OptimizationType.GAIN_DEFER,
                        symbol=symbol,
                        description=f"Large short-term gain of ${unrealized:.2f} — high tax impact",
                        action="Consider holding until long-term, or tax-loss harvest other positions",
                        estimated_tax_savings=unrealized * (self.short_term_rate - self.long_term_rate),
                        urgency="high",
                        details={
                            "unrealized_gain": unrealized,
                            "current_tax": unrealized * self.short_term_rate,
                            "ltcg_tax": unrealized * self.long_term_rate,
                        }
                    )
                    summary.opportunities.append(opp)
            else:
                loss = abs(unrealized)
                summary.total_unrealized_losses += loss
                if is_long_term:
                    summary.long_term_unrealized_losses += loss
                else:
                    summary.short_term_unrealized_losses += loss

                # Loss harvesting opportunity
                if not is_long_term and loss > 100:  # >$100 loss
                    opp = TaxOptimizationOpportunity(
                        type=OptimizationType.LOSS_HARVEST,
                        symbol=symbol,
                        description=f"Short-term loss of ${loss:.2f} — qualifies for harvest",
                        action=f"Sell {symbol} to harvest ${loss:.2f} loss",
                        estimated_tax_savings=loss * self.short_term_rate,
                        urgency="high" if loss > 500 else "medium",
                        details={
                            "unrealized_loss": loss,
                            "days_held": days_held,
                            "days_to_long_term": max(0, self.LONG_TERM_DAYS - days_held),
                        }
                    )
                    summary.opportunities.append(opp)
                    summary.harvestable_losses += loss

            # Check if near long-term threshold (applies to gains or losses)
            if not is_long_term:
                days_to_long_term = self.LONG_TERM_DAYS - days_held
                if 0 < days_to_long_term <= 30:
                    opp = TaxOptimizationOpportunity(
                        type=OptimizationType.HOLDING_PERIOD,
                        symbol=symbol,
                        description=f"Will become long-term in {days_to_long_term} days — saves taxes",
                        action=f"Hold {symbol} for {days_to_long_term} more days to qualify for LTCG rate",
                        estimated_tax_savings=unrealized * (self.short_term_rate - self.long_term_rate) if unrealized > 0 else 0,
                        urgency="medium",
                        details={
                            "unrealized_gain": unrealized if unrealized > 0 else 0,
                            "unrealized_loss": abs(unrealized) if unrealized < 0 else 0,
                            "days_to_long_term": days_to_long_term,
                            "current_rate": self.short_term_rate,
                            "projected_rate": self.long_term_rate,
                        }
                    )
                    summary.opportunities.append(opp)

        summary.net_unrealized = summary.total_unrealized_gains - summary.total_unrealized_losses
        return summary

    def get_loss_harvesting_candidates(
        self,
        positions: list[dict],
        min_loss: float = 100,
        current_date: Optional[datetime] = None
    ) -> list[TaxOptimizationOpportunity]:
        """
        Get positions with unrealized losses suitable for tax-loss harvesting.

        Args:
            positions: List of positions
            min_loss: Minimum loss threshold
            current_date: Analysis date

        Returns:
            List of loss harvesting opportunities
        """
        summary = self.analyze_portfolio_tax(positions, current_date)
        return [opp for opp in summary.opportunities if opp.type == OptimizationType.LOSS_HARVEST]

    def calculate_tax_liability(
        self,
        realized_gains: float,
        realized_losses: float,
        short_term_gains: float = 0,
        long_term_gains: float = 0,
        short_term_losses: float = 0,
        long_term_losses: float = 0,
        previous_year_carryover: float = 0,
        filing_status: str = "single"
    ) -> dict:
        """
        Calculate estimated tax liability.

        Args:
            realized_gains: Total realized gains
            realized_losses: Total realized losses
            short_term_gains: Short-term realized gains
            long_term_gains: Long-term realized gains
            short_term_losses: Short-term realized losses
            long_term_losses: Long-term realized losses
            previous_year_carryover: Loss carryover from previous year
            filing_status: Tax filing status

        Returns:
            Dict with tax calculation details
        """
        net_short = short_term_gains - short_term_losses
        net_long = long_term_gains - long_term_losses

        # Apply carryover losses
        remaining_carryover = previous_year_carryover
        if remaining_carryover > 0:
            if net_short > 0:
                used = min(remaining_carryover, net_short)
                net_short -= used
                remaining_carryover -= used
            if net_long > 0 and remaining_carryover > 0:
                used = min(remaining_carryover, net_long)
                net_long -= used
                remaining_carryover -= used

        # Annual loss limit ($3000 can be deducted against ordinary income)
        annual_deduction = min(3000, abs(net_short + net_long))

        # Net gains are taxed
        net_st_gain = max(0, net_short)
        net_lt_gain = max(0, net_long)

        tax_on_st = net_st_gain * self.short_term_rate
        tax_on_lt = net_lt_gain * self.long_term_rate

        total_tax = tax_on_st + tax_on_lt
        net_gain_after_tax = (net_st_gain + net_lt_gain) - total_tax

        return {
            "filing_status": filing_status,
            "short_term_gain": net_st_gain,
            "long_term_gain": net_lt_gain,
            "total_taxable_gain": net_st_gain + net_lt_gain,
            "short_term_tax": tax_on_st,
            "long_term_tax": tax_on_lt,
            "total_tax": total_tax,
            "net_gain_after_tax": net_gain_after_tax,
            "annual_loss_deduction": annual_deduction,
            "carryover_remaining": max(0, remaining_carryover - annual_deduction),
        }

    def get_asset_tax_efficiency(self, symbol: str, asset_type: str = "stock") -> AssetTaxEfficiency:
        """
        Get tax efficiency rating for an asset.

        Args:
            symbol: Asset symbol
            asset_type: Type of asset (stock, bond, ETF, REIT, fund)

        Returns:
            AssetTaxEfficiency rating
        """
        # Individual stocks = high efficiency (only taxed on sale)
        # ETFs = high efficiency (low turnover)
        # REITs = low efficiency (ordinary income)
        # Bonds = low efficiency (interest taxed as ordinary income)
        # Actively managed funds = medium-low (high turnover generates gains)
        # Keywords retained for future symbol-based classification
        # etf_keywords = ["ETF", "Index", "Growth", "Value"]
        # bond_keywords = ["Bond", "Income", "High Yield", "Muni"]
        # reit_keywords = ["REIT", "Real Estate"]

        if asset_type == "ETF":
            return AssetTaxEfficiency.HIGH
        elif asset_type == "stock":
            return AssetTaxEfficiency.HIGH
        elif asset_type == "REIT":
            return AssetTaxEfficiency.LOW
        elif asset_type == "bond":
            return AssetTaxEfficiency.LOW
        elif asset_type == "fund":
            return AssetTaxEfficiency.MEDIUM
        else:
            return AssetTaxEfficiency.MEDIUM

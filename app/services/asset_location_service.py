"""
Asset Location Service.

Optimizes asset placement across different account types to minimize taxes:
- Taxable accounts: Tax-efficient assets (growth stocks, ETFs)
- Tax-deferred (Traditional IRA, 401k): Tax-inefficient assets (bonds, REITs)
- Tax-free (Roth IRA): Highest growth potential assets
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AccountType(Enum):
    """Types of investment accounts."""
    TAXABLE = "taxable"
    TRADITIONAL_IRA = "traditional_ira"
    ROTH_IRA = "roth_ira"
    PLAN_401K = "401k"
    HSA = "hsa"


class AssetType(Enum):
    """Types of investment assets."""
    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    REIT = "reit"
    MUTUAL_FUND = "mutual_fund"
    MONEY_MARKET = "money_market"
    CRYPTO = "crypto"


@dataclass
class AccountInfo:
    """Information about an investment account."""
    account_id: str
    account_type: AccountType
    name: str
    balance: float = 0.0
    contributions_year: float = 0.0  # YTD contributions
    withdrawal_balance: float = 0.0  # Available for withdrawal without penalty


@dataclass
class Position:
    """A single position in a portfolio."""
    symbol: str
    asset_type: AssetType
    quantity: float
    current_price: float
    cost_basis: float
    annual_distribution: float = 0.0  # Dividends, interest
    turnover_rate: float = 0.0  # Annual turnover percentage


@dataclass
class AssetLocationRecommendation:
    """Recommendation for moving an asset to a different account."""
    symbol: str
    current_account: AccountType
    recommended_account: AccountType
    reason: str
    estimated_tax_savings: float
    quantity: float
    priority: str = "medium"  # low, medium, high


@dataclass
class AccountAllocation:
    """Recommended allocation for an account."""
    account_type: AccountType
    suggested_assets: list[str]  # Symbols
    target_allocation: dict[str, float]  # {asset_type: percentage}
    rationale: str


class AssetLocationService:
    """Service for optimizing asset location across accounts."""

    # Asset placement rules
    # Tax-efficient assets → Taxable accounts (low distributions, long holding)
    # Tax-inefficient assets → Tax-deferred (high distributions, bonds)
    # High-growth assets → Roth (tax-free growth)

    TAX_EFFICIENT = [AssetType.STOCK, AssetType.ETF]
    TAX_INEFFICIENT = [AssetType.BOND, AssetType.REIT, AssetType.MUTUAL_FUND]
    HIGH_GROWTH = [AssetType.STOCK, AssetType.ETF]

    def __init__(self):
        """Initialize Asset Location Service."""
        self.accounts: list[AccountInfo] = []
        self.positions: list[Position] = []

    def add_account(self, account: AccountInfo):
        """Add an account to analyze."""
        self.accounts.append(account)

    def add_position(self, position: Position):
        """Add a position to analyze."""
        self.positions.append(position)

    def get_recommendations(
        self,
        positions: list[Position],
        accounts: list[AccountInfo]
    ) -> list[AssetLocationRecommendation]:
        """
        Get asset location optimization recommendations.

        Args:
            positions: Current positions with account assignments
            accounts: All available accounts

        Returns:
            List of recommendations
        """
        recommendations = []
        tax_inefficient_in_taxable = []

        # Find tax-inefficient assets in taxable accounts
        for pos in positions:
            if pos.asset_type in self.TAX_INEFFICIENT:
                # Check if it's in a taxable account
                tax_inefficient_in_taxable.append(pos)

        # Generate recommendations
        for pos in tax_inefficient_in_taxable:
            annual_tax = pos.annual_distribution * 0.24  # Assume 24% marginal rate
            if annual_tax > 50:  # Only meaningful if >$50/year
                recommendations.append(AssetLocationRecommendation(
                    symbol=pos.symbol,
                    current_account=AccountType.TAXABLE,
                    recommended_account=AccountType.TRADITIONAL_IRA,
                    reason=f"{pos.asset_type.value} generates ${pos.annual_distribution:.2f}/yr in distributions — move to tax-deferred",
                    estimated_tax_savings=annual_tax,
                    quantity=pos.quantity,
                    priority="high" if annual_tax > 200 else "medium"
                ))

        # Check Roth placement opportunities
        high_growth_in_taxable = [
            p for p in positions
            if p.asset_type in self.HIGH_GROWTH and p.current_price > p.cost_basis
        ]

        for pos in high_growth_in_taxable:
            unrealized_gain = (pos.current_price - pos.cost_basis) * pos.quantity
            if unrealized_gain > 5000:
                # Suggest keeping high-growth in Roth for tax-free compounding
                recommendations.append(AssetLocationRecommendation(
                    symbol=pos.symbol,
                    current_account=AccountType.TAXABLE,
                    recommended_account=AccountType.ROTH_IRA,
                    reason=f"High-growth stock with ${unrealized_gain:.2f} unrealized gain — Roth offers tax-free growth",
                    estimated_tax_savings=unrealized_gain * 0.15,  # Estimated future LTCG tax
                    quantity=pos.quantity,
                    priority="medium"
                ))

        # Check Traditional IRA for high-turnover assets
        high_turnover_in_taxable = [
            p for p in positions
            if p.turnover_rate > 0.5  # >50% annual turnover
        ]

        for pos in high_turnover_in_taxable:
            if pos.asset_type not in [AssetType.BOND, AssetType.REIT]:
                recommendations.append(AssetLocationRecommendation(
                    symbol=pos.symbol,
                    current_account=AccountType.TAXABLE,
                    recommended_account=AccountType.TRADITIONAL_IRA,
                    reason=f"High turnover ({pos.turnover_rate:.0%}) — distributions in IRA avoid annual taxation",
                    estimated_tax_savings=pos.annual_distribution * 0.24,
                    quantity=pos.quantity,
                    priority="medium"
                ))

        return sorted(recommendations, key=lambda x: x.estimated_tax_savings, reverse=True)

    def get_account_allocations(
        self,
        total_portfolio_value: float,
        risk_profile: str = "moderate"
    ) -> dict[AccountType, AccountAllocation]:
        """
        Get recommended asset allocation by account type.

        Args:
            total_portfolio_value: Total portfolio value
            risk_profile: Risk profile (conservative, moderate, aggressive)

        Returns:
            Dict of account type to recommended allocation
        """
        # Target allocations by account type
        if risk_profile == "conservative":
            taxable_pct = 0.3
            trad_ira_pct = 0.4
            roth_pct = 0.1
            k401k_pct = 0.2
        elif risk_profile == "aggressive":
            taxable_pct = 0.5
            trad_ira_pct = 0.1
            roth_pct = 0.2
            k401k_pct = 0.2
        else:  # moderate
            taxable_pct = 0.4
            trad_ira_pct = 0.25
            roth_pct = 0.15
            k401k_pct = 0.2

        return {
            AccountType.TAXABLE: AccountAllocation(
                account_type=AccountType.TAXABLE,
                suggested_assets=["VTI", "SCHD", "QQQM", "Individual growth stocks"],
                target_allocation={
                    "stock": 0.7,
                    "etf": 0.3,
                },
                rationale="Tax-efficient assets with low distributions — ideal for taxable accounts"
            ),
            AccountType.TRADITIONAL_IRA: AccountAllocation(
                account_type=AccountType.TRADITIONAL_IRA,
                suggested_assets=["BND", "AGG", "VNQ", "High-yield bonds", "REITs"],
                target_allocation={
                    "bond": 0.6,
                    "reit": 0.3,
                    "stock": 0.1,
                },
                rationale="Tax-inefficient assets generate distributions taxed as ordinary income — sheltered in IRA"
            ),
            AccountType.ROTH_IRA: AccountAllocation(
                account_type=AccountType.ROTH_IRA,
                suggested_assets=["VGT", "ARKK", "Individual growth stocks", "Small-cap"],
                target_allocation={
                    "stock": 0.9,
                    "etf": 0.1,
                },
                rationale="Highest growth potential — tax-free compounding in Roth"
            ),
            AccountType.PLAN_401K: AccountAllocation(
                account_type=AccountType.PLAN_401K,
                suggested_assets=["Target date fund", "S&P 500 index", "International bonds"],
                target_allocation={
                    "mutual_fund": 0.5,
                    "bond": 0.3,
                    "stock": 0.2,
                },
                rationale="401k matches taxable bonds/REITs; maximize employer match first"
            ),
        }

    def calculate_location_savings(
        self,
        positions: list[Position],
        recommendations: list[AssetLocationRecommendation]
    ) -> dict:
        """
        Calculate estimated tax savings from implementing recommendations.

        Args:
            positions: Current positions
            recommendations: Location recommendations

        Returns:
            Summary of potential savings
        """
        total_savings = sum(r.estimated_tax_savings for r in recommendations)
        by_account = {}

        for rec in recommendations:
            acc = rec.recommended_account.value
            if acc not in by_account:
                by_account[acc] = 0.0
            by_account[acc] += rec.estimated_tax_savings

        return {
            "total_annual_tax_savings": total_savings,
            "by_account_type": by_account,
            "recommendations_count": len(recommendations),
            "high_priority_count": len([r for r in recommendations if r.priority == "high"]),
        }

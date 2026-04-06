"""
Estate Planning & Transfer Taxation Service
Estate value estimation, gift tax tracking, real estate integration, succession planning
"""

import math
from datetime import datetime, date
from typing import Optional
from uuid import UUID


class EstatePlanningService:
    """Service for estate planning and wealth transfer management."""

    # 2026 Taiwan estate tax rates (simplified)
    ESTATE_TAX_EXEMPTION = 16.193  # NTD millions (rough approximation)
    ESTATE_TAX_RATES = [
        (0.05, 60),      # 0-60M: 5%
        (0.10, 100),     # 60-100M: 10%
        (0.15, 200),     # 100-200M: 15%
        (0.20, 400),     # 200-400M: 20%
        (0.30, 600),     # 400-600M: 30%
        (0.40, 1000),    # 600M-1B: 40%
        (0.50, 99999999) # >1B: 50%
    ]

    # Taiwan annual gift tax exemption
    ANNUAL_GIFT_EXEMPTION_TWD = 244_000  # per recipient per year
    DAILY_GIFT_EXEMPTION_TWD = 22_000  # daily (de minimis)

    def __init__(self, db=None):
        self.db = db

    def calculate_estate_tax(
        self,
        total_estate_value: float,
        currency: str = "TWD",
        exchange_rate_to_twd: float = 31.5
    ) -> dict:
        """
        Calculate estimated estate tax liability.
        Simplified calculation based on Taiwan estate tax rules.
        """
        # Convert to TWD if needed
        value_in_twd = total_estate_value * exchange_rate_to_twd if currency != "TWD" else total_estate_value

        # Apply exemption
        taxable_estate = max(0, value_in_twd - self.ESTATE_TAX_EXEMPTION * 1_000_000)

        if taxable_estate <= 0:
            return {
                "total_estate_value": total_estate_value,
                "currency": currency,
                "value_in_twd": value_in_twd,
                "exemption_applied": self.ESTATE_TAX_EXEMPTION * 1_000_000,
                "taxable_estate": 0,
                "estimated_tax": 0,
                "effective_tax_rate": 0,
                "tax_bracket": "Exempt"
            }

        # Calculate progressive tax
        estimated_tax = 0
        remaining = taxable_estate
        previous_bracket_limit = 0

        for rate, bracket_limit in self.ESTATE_TAX_RATES:
            bracket_size = bracket_limit - previous_bracket_limit
            if remaining <= 0:
                break

            taxable_in_bracket = min(remaining, bracket_size)
            estimated_tax += taxable_in_bracket * rate
            remaining -= taxable_in_bracket
            previous_bracket_limit = bracket_limit

        effective_rate = (estimated_tax / value_in_twd * 100) if value_in_twd > 0 else 0

        return {
            "total_estate_value": total_estate_value,
            "currency": currency,
            "value_in_twd": value_in_twd,
            "exemption_applied": self.ESTATE_TAX_EXEMPTION * 1_000_000,
            "taxable_estate": taxable_estate,
            "estimated_tax": round(estimated_tax, 0),
            "estimated_tax_twd": round(estimated_tax, 0),
            "effective_tax_rate": f"{effective_rate:.2f}%",
            "tax_bracket": self._get_bracket_name(value_in_twd)
        }

    def _get_bracket_name(self, value_in_twd: float) -> str:
        """Get estate tax bracket name."""
        if value_in_twd < 60_000_000:
            return "5%"
        elif value_in_twd < 100_000_000:
            return "5-10%"
        elif value_in_twd < 200_000_000:
            return "10-15%"
        elif value_in_twd < 400_000_000:
            return "15-20%"
        elif value_in_twd < 600_000_000:
            return "20-30%"
        elif value_in_twd < 1_000_000_000:
            return "30-40%"
        else:
            return "40-50%"

    def calculate_gift_tax(
        self,
        gift_amount: float,
        recipient_relationship: str,
        annual_cumulative_gifts: float = 0,
        currency: str = "TWD"
    ) -> dict:
        """
        Calculate gift tax for a given gift.
        Based on Taiwan gift tax rules.
        """
        exemption = self.ANNUAL_GIFT_EXEMPTION_TWD
        tax_free_gifts = annual_cumulative_gifts + gift_amount

        if tax_free_gifts <= exemption:
            return {
                "gift_amount": gift_amount,
                "currency": currency,
                "annual_exemption": exemption,
                "cumulative_gifts": tax_free_gifts,
                "taxable_amount": 0,
                "estimated_tax": 0,
                "status": "Tax Free"
            }

        taxable = tax_free_gifts - exemption

        # Progressive tax rates for gifts
        if taxable < 2_500_000:
            tax = taxable * 0.04
        elif taxable < 5_000_000:
            tax = 100_000 + (taxable - 2_500_000) * 0.10
        elif taxable < 10_000_000:
            tax = 350_000 + (taxable - 5_000_000) * 0.15
        else:
            tax = 1_100_000 + (taxable - 10_000_000) * 0.20

        return {
            "gift_amount": gift_amount,
            "currency": currency,
            "annual_exemption": exemption,
            "cumulative_gifts": tax_free_gifts,
            "taxable_amount": taxable,
            "estimated_tax": round(tax, 0),
            "status": "Taxable"
        }

    def calculate_real_estate_yield(
        self,
        property_value: float,
        monthly_rent: float,
        currency: str = "USD"
    ) -> dict:
        """Calculate real estate rental yield metrics."""
        annual_rent = monthly_rent * 12
        gross_yield = (annual_rent / property_value * 100) if property_value > 0 else 0

        # Approximate expenses (property tax, maintenance, insurance)
        property_tax = property_value * 0.01  # ~1% annually
        maintenance = property_value * 0.01    # ~1% annually
        insurance = property_value * 0.003     # ~0.3% annually
        total_expenses = property_tax + maintenance + insurance

        net_yield = ((annual_rent - total_expenses) / property_value * 100) if property_value > 0 else 0

        return {
            "property_value": property_value,
            "monthly_rent": monthly_rent,
            "annual_rent": annual_rent,
            "currency": currency,
            "gross_yield": f"{gross_yield:.2f}%",
            "net_yield": f"{net_yield:.2f}%",
            "annual_expenses": round(total_expenses, 2),
            "expense_breakdown": {
                "property_tax": round(property_tax, 2),
                "maintenance": round(maintenance, 2),
                "insurance": round(insurance, 2)
            }
        }

    def calculate_life_insurance_needs(
        self,
        current_assets: float,
        current_debts: float,
        annual_income: float,
        years_to_protect: int,
        inflation_rate: float = 0.03,
        currency: str = "USD"
    ) -> dict:
        """
        Calculate life insurance needs based on income replacement method.
        """
        # Income replacement method: how much insurance to replace income for dependents
        total_income_needed = 0
        for year in range(years_to_protect):
            total_income_needed += annual_income * ((1 + inflation_rate) ** year)

        # Deduction for existing assets
        net_needed = max(0, total_income_needed - current_assets + current_debts)

        # Simple needs analysis
        debt_coverage = current_debts
        emergency_fund = annual_income * 0.5  # 6 months

        recommended_coverage = net_needed

        return {
            "current_assets": current_assets,
            "current_debts": current_debts,
            "annual_income": annual_income,
            "years_to_protect": years_to_protect,
            "currency": currency,
            "income_replacement_need": round(total_income_needed, 2),
            "recommended_coverage": round(recommended_coverage, 2),
            "debt_coverage_need": round(debt_coverage, 2),
            "emergency_fund_need": round(emergency_fund, 2),
            "total_need": round(recommended_coverage + debt_coverage + emergency_fund, 2)
        }

    def generate_estate_checklist(self, total_assets: float, has_spouse: bool = False) -> dict:
        """Generate estate planning checklist."""
        checklist = []

        # Basic documents
        checklist.append({
            "item": "Last Will and Testament",
            "priority": "critical",
            "completed": False,
            "notes": "Essential for asset distribution"
        })

        checklist.append({
            "item": "Power of Attorney",
            "priority": "critical",
            "completed": False,
            "notes": "For financial decisions if incapacitated"
        })

        checklist.append({
            "item": "Healthcare Directive",
            "priority": "critical",
            "completed": False,
            "notes": "Medical decision authority"
        })

        # Beneficiaries
        checklist.append({
            "item": "Review beneficiary designations",
            "priority": "high",
            "completed": False,
            "notes": "Ensure retirement accounts and insurance have correct beneficiaries"
        })

        # Trusts
        if total_assets > 50_000_000:
            checklist.append({
                "item": "Consider Revocable Living Trust",
                "priority": "high",
                "completed": False,
                "notes": "Avoids probate, manages assets if incapacitated"
            })

        # Property
        checklist.append({
            "item": "Property title review",
            "priority": "medium",
            "completed": False,
            "notes": "Ensure property deeds have correct ownership"
        })

        # Insurance review
        checklist.append({
            "item": "Life insurance policy review",
            "priority": "high",
            "completed": False,
            "notes": "Confirm coverage matches current needs"
        })

        # Digital assets
        checklist.append({
            "item": "Digital asset inventory",
            "priority": "medium",
            "completed": False,
            "notes": "List all online accounts and instructions"
        })

        return {
            "total_assets": total_assets,
            "has_spouse": has_spouse,
            "checklist": checklist,
            "critical_count": len([c for c in checklist if c["priority"] == "critical"]),
            "high_priority_count": len([c for c in checklist if c["priority"] == "high"]),
            "medium_priority_count": len([c for c in checklist if c["priority"] == "medium"])
        }

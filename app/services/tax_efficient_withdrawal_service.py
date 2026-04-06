"""
Tax-Efficient Withdrawal Service.

Optimizes retirement account withdrawal sequence to minimize taxes:
- Roth first (tax-free)
- Then taxable (capital gains treatment)
- Then Traditional IRA/401k (ordinary income)
- RMD planning
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class WithdrawalSource(Enum):
    """Source of retirement funds."""
    ROTH = "roth"
    TAXABLE = "taxable"
    TRADITIONAL_IRA = "traditional_ira"
    PLAN_401K = "401k"
    HSA = "hsa"


@dataclass
class AccountBalance:
    """Retirement account balance."""
    source: WithdrawalSource
    balance: float
    annual_distribution: float = 0.0  # Expected annual RMD/distribution
    rmd_age: Optional[int] = None  # Age when RMDs start
    tax_on_distributions: float = 0.0


@dataclass
class WithdrawalStep:
    """A single withdrawal step in the sequence."""
    step_number: int
    source: WithdrawalSource
    amount: float
    tax_impact: float
    rationale: str
    cumulative_tax: float


@dataclass
class WithdrawalPlan:
    """Complete withdrawal plan."""
    years: list["YearlyWithdrawal"]
    total_withdrawn: float = 0.0
    total_taxes_paid: float = 0.0
    effective_tax_rate: float = 0.0
    roth_percentage_at_end: float = 0.0  # Roth ratio at end


@dataclass
class YearlyWithdrawal:
    """Yearly withdrawal details."""
    year: int
    age: int
    withdrawal_steps: list[WithdrawalStep]
    total_withdrawn: float
    total_tax: float
    effective_tax_rate: float
    marginal_tax_rate: float
    rmd_required: float = 0.0


class TaxEfficientWithdrawalService:
    """Service for optimizing retirement withdrawal strategy."""

    # IRS RMD ages by birth year
    RMD_AGES = {
        1943: 72,
        1950: 72,
        1960: 72,
        1961: 73,  # SECURE 2.0 Act: born 1961+ = 73
        1966: 75,  # SECURE 2.0 Act: born 1966+ = 75
    }

    # Standard deduction by filing status (2024)
    STANDARD_DEDUCTION = {
        "single": 14600,
        "married_joint": 29200,
        "married_separate": 14600,
        "head_of_household": 21900,
    }

    # Tax brackets (2024, married joint example)
    TAX_BRACKETS_MJ = [
        (23200, 0.10),
        (94300, 0.12),
        (201050, 0.22),
        (383900, 0.24),
        (487450, 0.32),
        (731200, 0.35),
        (float("inf"), 0.37),
    ]

    TAX_BRACKETS_SINGLE = [
        (11600, 0.10),
        (47150, 0.12),
        (100525, 0.22),
        (191950, 0.24),
        (243725, 0.32),
        (609350, 0.35),
        (float("inf"), 0.37),
    ]

    def __init__(self, current_age: int, filing_status: str = "single"):
        """
        Initialize Withdrawal Service.

        Args:
            current_age: Current age
            filing_status: Tax filing status
        """
        self.current_age = current_age
        self.filing_status = filing_status
        self.accounts: list[AccountBalance] = []

    def add_account(self, account: AccountBalance):
        """Add a retirement account."""
        self.accounts.append(account)

    def get_rmd_age(self, birth_year: int) -> int:
        """Get RMD start age based on birth year."""
        if birth_year >= 1966:
            return 75
        elif birth_year >= 1961:
            return 73
        else:
            return 73  # Default to 73 for older

    def calculate_marginal_rate(
        self,
        taxable_income: float,
        brackets: Optional[list[tuple[float, float]]] = None
    ) -> float:
        """
        Calculate marginal tax rate for given taxable income.

        Args:
            taxable_income: Taxable income
            brackets: Tax brackets (default based on filing status)

        Returns:
            Marginal tax rate
        """
        if brackets is None:
            if self.filing_status == "married_joint":
                brackets = self.TAX_BRACKETS_MJ
            else:
                brackets = self.TAX_BRACKETS_SINGLE

        for threshold, rate in brackets:
            if taxable_income < threshold:
                return rate
        return brackets[-1][1]

    def calculate_tax(
        self,
        ordinary_income: float,
        capital_gains: float = 0,
        deductions: Optional[float] = None
    ) -> dict:
        """
        Calculate tax for given income.

        Args:
            ordinary_income: Ordinary income (wages, IRA distributions)
            capital_gains: Long-term capital gains
            deductions: Total deductions

        Returns:
            Tax calculation details
        """
        if deductions is None:
            deductions = self.STANDARD_DEDUCTION.get(self.filing_status, 14600)

        taxable_ordinary = max(0, ordinary_income - deductions)
        taxable_gains = max(0, capital_gains)

        # Ordinary income tax
        ordinary_tax = 0.0
        remaining = taxable_ordinary
        prev_threshold = 0
        brackets = self.TAX_BRACKETS_SINGLE if self.filing_status == "single" else self.TAX_BRACKETS_MJ
        for threshold, rate in brackets:
            if remaining <= 0:
                break
            bracket_size = threshold - prev_threshold
            taxable_in_bracket = min(remaining, bracket_size)
            ordinary_tax += taxable_in_bracket * rate
            remaining -= taxable_in_bracket
            prev_threshold = threshold

        # Capital gains tax (0%, 15%, 20%)
        if taxable_ordinary < 47025:  # 0% LTCG bracket
            ltcg_rate = 0.0
        elif taxable_ordinary < 518900:
            ltcg_rate = 0.15
        else:
            ltcg_rate = 0.20

        gains_tax = taxable_gains * ltcg_rate

        total_tax = ordinary_tax + gains_tax
        total_income = ordinary_income + capital_gains
        effective_rate = total_tax / total_income if total_income > 0 else 0.0

        return {
            "ordinary_income": ordinary_income,
            "capital_gains": capital_gains,
            "deductions": deductions,
            "taxable_ordinary": taxable_ordinary,
            "taxable_gains": taxable_gains,
            "ordinary_tax": ordinary_tax,
            "gains_tax": gains_tax,
            "total_tax": total_tax,
            "effective_rate": effective_rate,
            "marginal_rate": self.calculate_marginal_rate(taxable_ordinary),
            "ltcg_rate": ltcg_rate,
        }

    def generate_withdrawal_sequence(
        self,
        annual_expenses: float,
        start_year: int = 1,
        years_to_plan: int = 30,
        social_security_annual: float = 0,
        other_income_annual: float = 0,
    ) -> WithdrawalPlan:
        """
        Generate optimal withdrawal sequence.

        Args:
            annual_expenses: Annual expenses needed
            start_year: Years from now to start withdrawals
            years_to_plan: Number of years to plan
            social_security_annual: Annual Social Security benefit
            other_income_annual: Other fixed annual income

        Returns:
            WithdrawalPlan with yearly steps
        """
        yearly_plan = []
        cumulative_tax = 0.0
        cumulative_withdrawn = 0.0

        # Sort accounts by withdrawal priority
        # 1. Roth (tax-free growth, no RMDs)
        # 2. Taxable (favorable capital gains treatment)
        # 3. Traditional IRA / 401k (ordinary income, RMDs)
        # 4. HSA (triple tax advantage, last resort)

        remaining_expenses = annual_expenses - social_security_annual - other_income_annual
        roth_balance = sum(a.balance for a in self.accounts if a.source == WithdrawalSource.ROTH)
        taxable_balance = sum(a.balance for a in self.accounts if a.source == WithdrawalSource.TAXABLE)
        trad_balance = sum(a.balance for a in self.accounts if a.source == WithdrawalSource.TRADITIONAL_IRA)
        k401k_balance = sum(a.balance for a in self.accounts if a.source == WithdrawalSource.PLAN_401K)
        hsa_balance = sum(a.balance for a in self.accounts if a.source == WithdrawalSource.HSA)

        for year in range(start_year, start_year + years_to_plan):
            age = self.current_age + year
            steps = []
            total_needed = max(0, remaining_expenses)  # Adjust for inflation
            total_withdrawn_year = 0.0
            total_tax_year = 0.0

            # Roth withdrawals (tax-free)
            if roth_balance > 0 and total_needed > 0:
                roth_amount = min(roth_balance, total_needed)
                steps.append(WithdrawalStep(
                    step_number=1,
                    source=WithdrawalSource.ROTH,
                    amount=roth_amount,
                    tax_impact=0.0,
                    rationale="Roth withdrawals are tax-free — use first",
                    cumulative_tax=cumulative_tax
                ))
                total_withdrawn_year += roth_amount
                total_needed -= roth_amount
                roth_balance -= roth_amount

            # Taxable account (capital gains treatment)
            if taxable_balance > 0 and total_needed > 0:
                taxable_amount = min(taxable_balance, total_needed)
                # Assume long-term gains portion
                gains_pct = 0.7  # 70% of taxable account is gains
                gains_amount = taxable_amount * gains_pct

                gains_tax = gains_amount * 0.15  # LTCG rate
                tax_on_taxable = gains_tax

                steps.append(WithdrawalStep(
                    step_number=2,
                    source=WithdrawalSource.TAXABLE,
                    amount=taxable_amount,
                    tax_impact=tax_on_taxable,
                    rationale="Taxable account — only capital gains portion taxed at LTCG rate",
                    cumulative_tax=cumulative_tax + tax_on_taxable
                ))
                total_withdrawn_year += taxable_amount
                total_tax_year += tax_on_taxable
                total_needed -= taxable_amount
                taxable_balance -= taxable_amount

            # Traditional IRA (ordinary income, RMDs required)
            rmd_amount = 0.0
            if trad_balance > 0:
                # Calculate RMD
                rmd_rate = 1.0 / max(1, 27 - (age - 72))  # Simplified divisor
                rmd_amount = min(trad_balance, trad_balance * rmd_rate)

                if total_needed > 0:
                    trad_to_withdraw = min(trad_balance, total_needed)
                    tax_on_trad = self.calculate_marginal_rate(
                        social_security_annual + other_income_annual + trad_to_withdraw
                    ) * trad_to_withdraw

                    steps.append(WithdrawalStep(
                        step_number=3,
                        source=WithdrawalSource.TRADITIONAL_IRA,
                        amount=trad_to_withdraw,
                        tax_impact=tax_on_trad,
                        rationale=f"Traditional IRA — ordinary income tax. RMD: ${rmd_amount:.0f}",
                        cumulative_tax=cumulative_tax + tax_on_trad
                    ))
                    total_withdrawn_year += trad_to_withdraw
                    total_tax_year += tax_on_trad
                    total_needed -= trad_to_withdraw
                    trad_balance -= trad_to_withdraw
                    cumulative_tax += tax_on_trad

            # 401k
            if k401k_balance > 0 and total_needed > 0:
                k401k_to_withdraw = min(k401k_balance, total_needed)
                tax_on_401k = self.calculate_marginal_rate(
                    social_security_annual + other_income_annual + k401k_to_withdraw
                ) * k401k_to_withdraw

                steps.append(WithdrawalStep(
                    step_number=4,
                    source=WithdrawalSource.PLAN_401K,
                    amount=k401k_to_withdraw,
                    tax_impact=tax_on_401k,
                    rationale="401k — ordinary income tax (consider Roth conversion before depletion)",
                    cumulative_tax=cumulative_tax + tax_on_401k
                ))
                total_withdrawn_year += k401k_to_withdraw
                total_tax_year += tax_on_401k
                k401k_balance -= k401k_to_withdraw

            # HSA last (medical expenses only)
            if hsa_balance > 0 and total_needed > 0:
                hsa_to_withdraw = min(hsa_balance, total_needed)
                steps.append(WithdrawalStep(
                    step_number=5,
                    source=WithdrawalSource.HSA,
                    amount=hsa_to_withdraw,
                    tax_impact=0.0 if total_needed < 5000 else hsa_to_withdraw * 0.10,
                    rationale="HSA — tax-free for medical. Non-medical taxable as ordinary income.",
                    cumulative_tax=cumulative_tax
                ))
                total_withdrawn_year += hsa_to_withdraw

            effective_rate = total_tax_year / total_withdrawn_year if total_withdrawn_year > 0 else 0.0
            marginal_rate = self.calculate_marginal_rate(
                social_security_annual + other_income_annual + total_withdrawn_year
            )

            yearly_plan.append(YearlyWithdrawal(
                year=year,
                age=age,
                withdrawal_steps=steps,
                total_withdrawn=total_withdrawn_year,
                total_tax=total_tax_year,
                effective_tax_rate=effective_rate,
                marginal_tax_rate=marginal_rate,
                rmd_required=rmd_amount
            ))

            cumulative_withdrawn += total_withdrawn_year
            cumulative_tax += total_tax_year

        # Adjust expenses for inflation
        remaining_expenses = annual_expenses * 1.02 ** (start_year - 1)  # 2% inflation

        return WithdrawalPlan(
            years=yearly_plan,
            total_withdrawn=cumulative_withdrawn,
            total_taxes_paid=cumulative_tax,
            effective_tax_rate=cumulative_tax / cumulative_withdrawn if cumulative_withdrawn > 0 else 0.0,
            roth_percentage_at_end=roth_balance / max(1, roth_balance + taxable_balance + trad_balance + k401k_balance)
        )

    def calculate_roth_conversion_analysis(
        self,
        trad_ira_balance: float,
        current_marginal_rate: float,
        target_marginal_rate: float,
        years_until_rmd: int
    ) -> dict:
        """
        Analyze Roth conversion strategy.

        Args:
            trad_ira_balance: Traditional IRA balance
            current_marginal_rate: Current marginal tax rate
            target_marginal_rate: Expected future marginal tax rate
            years_until_rmd: Years until RMDs start

        Returns:
            Roth conversion analysis
        """
        # Cost to convert now at current rate
        conversion_cost = trad_ira_balance * current_marginal_rate

        # Cost of RMDs at future rates (simplified)
        # Assume RMDs pushed into higher brackets later
        total_rmd_tax = 0.0
        remaining = trad_ira_balance
        for i in range(years_until_rmd):
            rmd = remaining / (27 - i)  # Approximate RMD
            rmd_tax = rmd * target_marginal_rate
            total_rmd_tax += rmd_tax
            remaining -= rmd

        savings = total_rmd_tax - conversion_cost
        breakeven_convert_pct = (total_rmd_tax / conversion_cost) if conversion_cost > 0 else 1.0

        return {
            "trad_ira_balance": trad_ira_balance,
            "current_marginal_rate": current_marginal_rate,
            "target_marginal_rate": target_marginal_rate,
            "cost_to_convert_now": conversion_cost,
            "estimated_future_rmd_tax": total_rmd_tax,
            "net_savings": savings,
            "recommendation": "convert" if savings > 0 else "wait",
            "breakeven_conversion_percentage": breakeven_convert_pct * 100,
        }

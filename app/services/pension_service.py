"""
Pension / 劳保 Integration Service

Estimates retirement gap and provides projections based on:
- 劳保 (Labor Insurance) data
- 月退俸 (Monthly pension) estimates
- Monte Carlo simulation (reused from Phase 20)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.services.monte_carlo_service import MonteCarloService


# 劳保 pension formula constants (2024)
LABOR_INSURANCE_PENSION_PARAMS = {
    # 投保薪資 average (最高60個月)
    "avg_salary_months": 60,
    # 年資給付率 (per year of contribution)
    "annual_rate": 0.00175,  # 1.55% × 1.1 for 2024
    # 月退俸 floor
    "monthly_min": 5000,
    # 一次金 calculation: avg_salary × years × 1.55
    "lump_sum_rate": 0.0155,
    # Contribution ceiling (雇主+employee share ~10%)
    "contribution_rate": 0.10,
    # Max insured salary (2024: 45,800)
    "max_insured_salary": 45800,
    # Min insured salary (2024: 27,470)
    "min_insured_salary": 27470,
}

# Taiwan life expectancy (2024)
TAIWAN_LIFE_EXPECTANCY = {
    "male": 79.8,
    "female": 85.2,
    "retirement_age_male": 65,
    "retirement_age_female": 63,  # 漸進延後
}

# Annual inflation assumption
INFLATION_RATE = 0.03

# Safe withdrawal rate
SAFE_WITHDRAWAL_RATE = 0.04


@dataclass
class LaborInsuranceSummary:
    """Summary of Labor Insurance (劳保) pension entitlements."""
    labor_insurance_number: str
    insured_salary: float  # 投保薪資
    years_contributed: int  # 年資
    months_contributed: int  # 月數
    average_insured_salary: float  # 平均投保薪資 (最高60個月)
    estimated_monthly_pension: float  # 月退俸估計
    estimated_lump_sum: float  # 一次請領估計
    retirement_eligibility: bool  # 是否符合請領資格
    eligible_date: Optional[str]  # 預計可請領日期
    contribution_history: list[dict] = field(default_factory=list)
    source: str = "labor_bureau"


@dataclass
class RetirementGapAnalysis:
    """Analysis of retirement savings gap."""
    current_age: int
    retirement_age: int
    life_expectancy: int
    years_to_retirement: int
    years_in_retirement: int

    # Current savings
    current_savings: float
    monthly_contribution: float  # Current monthly contribution to retirement
    estimated_pension_monthly: float  # From 劳保

    # Projections (inflation-adjusted)
    projected_savings_at_retirement: float
    projected_total_pension: float  # Total pension over retirement
    projected_total_needs: float  # Total estimated needs

    # Gap analysis
    monthly_income_gap: float  # Monthly shortage
    total_gap: float  # Total savings gap
    gap_percentage: float  # Gap as % of needs
    is_on_track: bool  # True if gap <= 0

    # Monte Carlo simulation
    monte_carlo_result: Optional[dict] = None

    # Recommendations
    recommendations: list[str] = field(default_factory=list)


@dataclass
class PensionProjection:
    """Complete pension projection result."""
    labor_insurance: LaborInsuranceSummary
    gap_analysis: RetirementGapAnalysis
    monthly_budget_recommendation: dict
    action_items: list[dict]
    timestamp: str


class PensionService:
    """
    Service for estimating retirement gaps and providing pension projections.

    Integrates:
    - 劳保 (Labor Insurance) pension estimates via Open Finance API
    - Monte Carlo simulation (from Phase 20) for market-based projections
    - Gap analysis comparing projected income vs retirement needs
    """

    def __init__(self, open_finance_adapter=None, monte_carlo_service: Optional[MonteCarloService] = None):
        """Initialize Pension Service.
        
        Args:
            open_finance_adapter: Optional OpenFinanceAdapter instance
            monte_carlo_service: Optional MonteCarloService instance (Phase 20)
        """
        from app.services.open_finance_adapter import OpenFinanceAdapter
        self.adapter = open_finance_adapter or OpenFinanceAdapter()
        self.monte_carlo = monte_carlo_service or MonteCarloService()

    async def get_pension_data(
        self,
        citizen_id: str,
        labor_insurance_number: str,
    ) -> LaborInsuranceSummary:
        """
        Fetch and calculate 劳保 pension entitlements.

        Args:
            citizen_id: National ID
            labor_insurance_number: 劳保號碼

        Returns:
            LaborInsuranceSummary with pension estimates
        """
        # Fetch raw pension data from Open Finance adapter
        raw_data = await self.adapter.get_pension_data(
            citizen_id=citizen_id,
            labor_insurance_number=labor_insurance_number,
        )

        # Calculate estimated pension using 劳保 formula
        insured_salary = raw_data.insured_salary or self._get_default_insured_salary()
        years = raw_data.years_contributed or 0

        # Check eligibility (需年滿65，且投保年資滿15年)
        eligible = years >= 15
        eligible_date = None
        if not eligible and years > 0:
            # Estimate when eligibility will be reached
            remaining_years = 15 - years
            eligible_year = datetime.now().year + remaining_years
            eligible_date = f"{eligible_year}-01-01"

        # 月退俸 formula: avg_salary × years × 1.55% × 1.1
        annual_rate = LABOR_INSURANCE_PENSION_PARAMS["annual_rate"]
        monthly_pension = (
            insured_salary
            * years
            * annual_rate
            * 12
        ) / 12
        monthly_pension = max(monthly_pension, LABOR_INSURANCE_PENSION_PARAMS["monthly_min"])

        # 一次金 formula: avg_salary × years × 1.55
        lump_sum = insured_salary * years * LABOR_INSURANCE_PENSION_PARAMS["lump_sum_rate"]

        return LaborInsuranceSummary(
            labor_insurance_number=labor_insurance_number,
            insured_salary=insured_salary,
            years_contributed=years,
            months_contributed=years * 12,
            average_insured_salary=insured_salary,
            estimated_monthly_pension=round(monthly_pension, 2),
            estimated_lump_sum=round(lump_sum, 2),
            retirement_eligibility=eligible,
            eligible_date=eligible_date,
            contribution_history=raw_data.contribution_history,
            source="esun_bank",
        )

    async def analyze_retirement_gap(
        self,
        citizen_id: str,
        labor_insurance_number: str,
        current_age: int,
        retirement_age: int = 65,
        current_savings: float = 0,
        monthly_contribution: float = 0,
        current_salary: float = 0,
        monthly_expenses: float = 0,
        gender: str = "male",
        use_monte_carlo: bool = True,
    ) -> PensionProjection:
        """
        Analyze retirement gap with full projections.

        Args:
            citizen_id: National ID
            labor_insurance_number: 劳保號碼
            current_age: Current age
            retirement_age: Target retirement age
            current_savings: Current retirement savings
            monthly_contribution: Monthly retirement contribution
            current_salary: Current monthly salary
            monthly_expenses: Current monthly expenses
            gender: male or female
            use_monte_carlo: Whether to run Monte Carlo simulation

        Returns:
            PensionProjection with full analysis
        """
        # Get 劳保 pension estimate
        labor_insurance = await self.get_pension_data(citizen_id, labor_insurance_number)

        # Get life expectancy
        life_exp = TAIWAN_LIFE_EXPECTANCY.get(
            gender.lower(),
            TAIWAN_LIFE_EXPECTANCY["male"]
        )

        years_to_retirement = retirement_age - current_age
        years_in_retirement = int(life_exp - retirement_age)

        # Inflation-adjust expenses
        inflated_expenses = self._inflate(monthly_expenses, years_to_retirement)
        monthly_needs = inflated_expenses

        # Project savings growth (assume 5% annual return)
        projected_savings = self._project_savings(
            current_savings,
            monthly_contribution,
            years_to_retirement,
            annual_return=0.05,
        )

        # Project pension total over retirement
        pension_monthly = labor_insurance.estimated_monthly_pension
        total_pension = pension_monthly * 12 * years_in_retirement

        # Calculate gaps
        # Monthly retirement income = pension + safe withdrawal from savings
        safe_withdrawal = projected_savings * SAFE_WITHDRAWAL_RATE / 12
        monthly_income = pension_monthly + safe_withdrawal
        monthly_gap = monthly_needs - monthly_income
        total_gap = monthly_gap * 12 * years_in_retirement
        gap_pct = (monthly_gap / monthly_needs) * 100 if monthly_needs > 0 else 0
        is_on_track = monthly_gap <= 0

        # Monte Carlo simulation (reuse Phase 20)
        monte_carlo_result = None
        if use_monte_carlo and current_savings > 0:
            try:
                from app.schemas.schemas import RetirementSimulationRequest
                request = RetirementSimulationRequest(
                    current_age=current_age,
                    retirement_age=retirement_age,
                    current_savings=current_savings,
                    monthly_contribution=monthly_contribution,
                    desired_monthly_income=monthly_needs,
                    portfolio_allocation={"stocks": 0.6, "bonds": 0.3, "cash": 0.1},
                    num_simulations=1000,
                    years_to_simulate=years_in_retirement,
                )
                mc_result = self.monte_carlo.run_retirement_simulation(request)
                monte_carlo_result = {
                    "success_probability": mc_result.success_probability,
                    "median_outcome": mc_result.median_outcome,
                    "percentile_10": mc_result.percentile_10,
                    "percentile_90": mc_result.percentile_90,
                    "average_outcome": mc_result.average_outcome,
                }
            except Exception:
                monte_carlo_result = None

        # Build gap analysis
        gap_analysis = RetirementGapAnalysis(
            current_age=current_age,
            retirement_age=retirement_age,
            life_expectancy=int(life_exp),
            years_to_retirement=years_to_retirement,
            years_in_retirement=years_in_retirement,
            current_savings=current_savings,
            monthly_contribution=monthly_contribution,
            estimated_pension_monthly=pension_monthly,
            projected_savings_at_retirement=round(projected_savings, 2),
            projected_total_pension=round(total_pension, 2),
            projected_total_needs=round(monthly_needs * 12 * years_in_retirement, 2),
            monthly_income_gap=round(monthly_gap, 2),
            total_gap=round(total_gap, 2),
            gap_percentage=round(gap_pct, 2),
            is_on_track=is_on_track,
            monte_carlo_result=monte_carlo_result,
            recommendations=self._generate_recommendations(
                monthly_gap=monthly_gap,
                gap_pct=gap_pct,
                is_on_track=is_on_track,
                pension_monthly=pension_monthly,
                monthly_contribution=monthly_contribution,
            ),
        )

        # Monthly budget recommendation
        monthly_budget = {
            "needs": round(monthly_needs, 2),  # Housing, food, healthcare
            "wants": round(current_salary * 0.20, 2),  # Discretionary
            "savings": round(monthly_contribution + max(0, -monthly_gap), 2),
            "note": "Based on 50/30/20 rule, adjusted for retirement gap",
        }

        # Action items
        action_items = self._generate_action_items(
            gap_analysis=gap_analysis,
            labor_insurance=labor_insurance,
            years_to_retirement=years_to_retirement,
            projected_savings=projected_savings,
        )

        return PensionProjection(
            labor_insurance=labor_insurance,
            gap_analysis=gap_analysis,
            monthly_budget_recommendation=monthly_budget,
            action_items=action_items,
            timestamp=datetime.now().isoformat(),
        )

    # ─── Helper methods ───────────────────────────────────────────────────

    def _get_default_insured_salary(self) -> float:
        """Get default insured salary for estimation."""
        return LABOR_INSURANCE_PENSION_PARAMS["max_insured_salary"]

    def _inflate(self, amount: float, years: int, rate: float = INFLATION_RATE) -> float:
        """Inflate amount over years at given rate."""
        return amount * ((1 + rate) ** years)

    def _project_savings(
        self,
        current: float,
        monthly: float,
        years: int,
        annual_return: float = 0.05,
    ) -> float:
        """Project savings with monthly contributions and annual return."""
        monthly_return = annual_return / 12
        months = years * 12

        # Future value of current savings
        fv_current = current * ((1 + monthly_return) ** months)

        # Future value of monthly contributions (annuity)
        if monthly_return > 0:
            fv_contribs = monthly * (((1 + monthly_return) ** months) - 1) / monthly_return
        else:
            fv_contribs = monthly * months

        return fv_current + fv_contribs

    def _generate_recommendations(
        self,
        monthly_gap: float,
        gap_pct: float,
        is_on_track: bool,
        pension_monthly: float,
        monthly_contribution: float,
    ) -> list[str]:
        """Generate personalized retirement recommendations."""
        recommendations = []

        if is_on_track:
            recommendations.append("✓ 您目前的退休規劃進度良好，繼續維持當前储蓄比例")
        else:
            if monthly_gap > 0:
                recommendations.append(
                    f"⚠️ 預估每月缺口 {monthly_gap:,.0f} 元，需增加 retirement savings"
                )

            if gap_pct > 50:
                recommendations.append(
                    "🔴 退休缺口過大，建議立即提高 retirement contribution 至少10%"
                )
            elif gap_pct > 20:
                recommendations.append(
                    "🟡 退休缺口明顯，建議增加 retirement savings 5-10%"
                )

        if pension_monthly < 20000:
            recommendations.append(
                "💡 您的劳保月退俸較低，建議考慮自願提高投保薪資或增加個人 retirement account"
            )

        if monthly_contribution < 6000:
            recommendations.append(
                "💡 建議利用勞退自提制度，雇主也會對應提撥6%"
            )

        recommendations.append(
            "📊 建議使用我們的Monte Carlo模擬工具進行更精確的退休預測"
        )

        return recommendations

    def _generate_action_items(
        self,
        gap_analysis: RetirementGapAnalysis,
        labor_insurance: LaborInsuranceSummary,
        years_to_retirement: int,
        projected_savings: float,
    ) -> list[dict]:
        """Generate actionable items to close retirement gap."""
        items = []

        if not labor_insurance.retirement_eligibility:
            items.append({
                "priority": "HIGH",
                "action": "確認劳保年資",
                "detail": f"目前年資 {labor_insurance.years_contributed} 年，需滿15年才能請領。預計 {labor_insurance.eligible_date} 可符合資格",
            })

        if gap_analysis.monthly_income_gap > 0:
            # Calculate required additional monthly savings
            # PV of gap over retirement years at 4% SWR
            years_in_ret = gap_analysis.years_in_retirement
            if years_in_ret > 0 and years_to_retirement > 0:
                required_additional = (
                    gap_analysis.monthly_income_gap
                    * 12
                    * years_in_ret
                    * 0.04
                    / ((1.05 ** years_to_retirement - 1) / 0.05 * 12)
                ) if years_to_retirement > 0 else 0

                items.append({
                    "priority": "HIGH",
                    "action": "增加月儲蓄",
                    "detail": f"建議每月額外儲蓄 {max(0, required_additional):,.0f} 元以弥补退休缺口",
                })

        if not gap_analysis.is_on_track:
            items.append({
                "priority": "MEDIUM",
                "action": "評估延後退休",
                "detail": f"若延後 {min(5, years_to_retirement)} 年退休，可大幅减少缺口",
            })

        items.append({
            "priority": "MEDIUM",
            "action": "検討安盛/#{self._get_voluntary_contribution_advice(gap_analysis)}",
            "detail": "了解自願提高劳保投保薪資的選項，增加未來月退俸",
        })

        return items

    def _get_voluntary_contribution_advice(self, gap_analysis: RetirementGapAnalysis) -> str:
        """Get advice on voluntary contribution increases."""
        if gap_analysis.gap_percentage > 30:
            return "High"
        elif gap_analysis.gap_percentage > 10:
            return "Medium"
        return "Low"

    async def estimate_pension_from_salary(
        self,
        monthly_salary: float,
        years_contributed: int,
        contribution_rate: float = 0.10,
    ) -> dict:
        """
        Estimate pension entitlements from salary and years of contribution.

        Useful when actual 劳保 data is not available.
        
        Args:
            monthly_salary: Monthly salary (used to estimate 投保薪資)
            years_contributed: Years of labor insurance contribution
            contribution_rate: Employer+employee contribution rate (default 10%)

        Returns:
            Dict with pension estimates
        """
        # Estimate insured salary from monthly salary
        insured_salary = min(
            monthly_salary,
            LABOR_INSURANCE_PENSION_PARAMS["max_insured_salary"]
        )

        # Monthly pension formula
        annual_rate = LABOR_INSURANCE_PENSION_PARAMS["annual_rate"]
        monthly_pension = (
            insured_salary
            * years_contributed
            * annual_rate
            * 12
        ) / 12

        monthly_pension = max(monthly_pension, LABOR_INSURANCE_PENSION_PARAMS["monthly_min"])

        # Lump sum
        lump_sum = insured_salary * years_contributed * LABOR_INSURANCE_PENSION_PARAMS["lump_sum_rate"]

        # Replacement rate
        replacement_rate = (monthly_pension / insured_salary) * 100 if insured_salary > 0 else 0

        return {
            "estimated_insured_salary": insured_salary,
            "years_contributed": years_contributed,
            "monthly_pension_estimate": round(monthly_pension, 2),
            "lump_sum_estimate": round(lump_sum, 2),
            "replacement_rate": round(replacement_rate, 2),
            "is_eligible": years_contributed >= 15,
            "note": "基於薪資估算，實際數據請以劳保局提供為準",
        }

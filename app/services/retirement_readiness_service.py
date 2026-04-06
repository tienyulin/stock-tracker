"""
Retirement Readiness Service

Provides retirement readiness assessment by integrating with
GoalMonitoringService and analyzing user's financial profile.
"""

from datetime import datetime
from typing import Optional

from app.schemas.agent_schemas import (
    PersonalFinancialProfile,
    RetirementGapResult,
    RetirementReadinessResult,
)
from app.services.goal_monitoring_service import GoalMonitoringService


class RetirementReadinessService:
    """Service to assess retirement readiness and provide improvement suggestions."""

    # Readability score thresholds
    SCORE_EXCELLENT = 85
    SCORE_GOOD = 70
    SCORE_MODERATE = 50
    SCORE_LOW = 30

    def __init__(self, db=None):
        self.db = db
        self.goal_service = GoalMonitoringService(db) if db else None

    async def assess_retirement_readiness(
        self,
        profile: PersonalFinancialProfile,
        current_savings: float,
        annual_expenses: float,
        retirement_age: int = 65,
    ) -> RetirementReadinessResult:
        """Assess retirement readiness based on user's financial profile.

        Args:
            profile: User's personal financial profile.
            current_savings: Current retirement savings amount.
            annual_expenses: Estimated annual expenses in retirement.
            retirement_age: Target retirement age.

        Returns:
            RetirementReadinessResult with score and suggestions.
        """
        years_to_retirement = max(0, retirement_age - profile.age)

        # Calculate required nest egg (25x annual expenses = 4% safe withdrawal rate)
        required_nest_egg = annual_expenses * 25

        # Calculate monthly contribution needed
        if years_to_retirement > 0:
            # Assuming 7% annual return
            monthly_return = 0.07 / 12
            n_months = years_to_retirement * 12
            # FV of current savings + PV of monthly contributions = required
            # Solve for monthly contribution
            fv_current = current_savings * ((1 + monthly_return) ** n_months)
            remaining = required_nest_egg - fv_current
            if remaining > 0 and n_months > 0:
                monthly_contribution_needed = remaining / (((1 + monthly_return) ** n_months - 1) / monthly_return)
            else:
                monthly_contribution_needed = 0.0
        else:
            monthly_contribution_needed = 0.0 if current_savings >= required_nest_egg else float('inf')

        # Calculate readiness score
        readiness_score = self._calculate_score(
            current_savings=current_savings,
            required_nest_egg=required_nest_egg,
            profile=profile,
            years_to_retirement=years_to_retirement,
        )

        # Determine readiness level
        readiness_level = self._determine_level(readiness_score)

        # Identify key factors
        key_factors = self._identify_key_factors(
            profile=profile,
            current_savings=current_savings,
            required_nest_egg=required_nest_egg,
            years_to_retirement=years_to_retirement,
        )

        # Generate improvement suggestions
        suggestions = self._generate_suggestions(
            profile=profile,
            current_savings=current_savings,
            required_nest_egg=required_nest_egg,
            monthly_contribution_needed=monthly_contribution_needed,
            years_to_retirement=years_to_retirement,
            readiness_score=readiness_score,
        )

        return RetirementReadinessResult(
            readiness_score=readiness_score,
            readiness_level=readiness_level,
            current_nest_egg=current_savings,
            on_track_nest_egg=required_nest_egg,
            monthly_contribution_needed=monthly_contribution_needed,
            years_to_retirement=years_to_retirement,
            key_factors=key_factors,
            improvement_suggestions=suggestions,
            confidence=self._calculate_confidence(profile, years_to_retirement),
            assessed_at=datetime.utcnow(),
        )

    def _calculate_score(
        self,
        current_savings: float,
        required_nest_egg: float,
        profile: PersonalFinancialProfile,
        years_to_retirement: int,
    ) -> float:
        """Calculate readiness score 0-100."""
        if required_nest_egg <= 0:
            return 100.0

        # Base score from savings ratio
        savings_ratio = min(current_savings / required_nest_egg, 1.0)
        base_score = savings_ratio * 60  # Up to 60 points from savings

        # Additional points for time factor
        if years_to_retirement > 0:
            # If young and saving, bonus points
            if profile.age < 40 and profile.monthly_income > 0:
                savings_rate = (profile.monthly_savings or 0) / profile.monthly_income
                if savings_rate >= 0.20:
                    base_score += 15
                elif savings_rate >= 0.10:
                    base_score += 10
                else:
                    base_score += 5
        else:
            # Close to retirement, savings ratio matters more
            base_score = savings_ratio * 100

        # Bonus for diversified income
        if profile.passive_income_monthly and profile.passive_income_monthly > 0:
            base_score += 10

        # Bonus for emergency fund
        if profile.has_emergency_fund:
            base_score += 10

        return min(base_score, 100.0)

    def _determine_level(self, score: float) -> str:
        """Determine readiness level from score."""
        if score >= self.SCORE_EXCELLENT:
            return "on_track"
        elif score >= self.SCORE_GOOD:
            return "moderate_gap"
        elif score >= self.SCORE_MODERATE:
            return "significant_gap"
        else:
            return "off_track"

    def _identify_key_factors(
        self,
        profile: PersonalFinancialProfile,
        current_savings: float,
        required_nest_egg: float,
        years_to_retirement: int,
    ) -> list[str]:
        """Identify key factors affecting retirement readiness."""
        factors = []

        # Savings rate factor
        if profile.monthly_income > 0 and profile.monthly_savings:
            rate = profile.monthly_savings / profile.monthly_income
            if rate >= 0.20:
                factors.append("high_savings_rate")
            elif rate >= 0.10:
                factors.append("moderate_savings_rate")
            else:
                factors.append("low_savings_rate")

        # Emergency fund
        if profile.has_emergency_fund:
            factors.append("emergency_fund_in_place")

        # Passive income
        if profile.passive_income_monthly and profile.passive_income_monthly > 0:
            factors.append("has_passive_income")

        # Debt status
        if profile.total_debt and profile.total_debt > profile.monthly_income * 12:
            factors.append("high_debt_burden")
        elif profile.total_debt and profile.total_debt > 0:
            factors.append("has_debt")

        # Investment allocation (assuming diversified if age-appropriate)
        if profile.risk_tolerance in ("aggressive", "moderate"):
            factors.append("appropriate_risk_tolerance")

        # Time factor
        if years_to_retirement > 20:
            factors.append("long_compounding_window")
        elif years_to_retirement < 10:
            factors.append("short_time_horizon")

        return factors

    def _generate_suggestions(
        self,
        profile: PersonalFinancialProfile,
        current_savings: float,
        required_nest_egg: float,
        monthly_contribution_needed: float,
        years_to_retirement: int,
        readiness_score: float,
    ) -> list[str]:
        """Generate actionable improvement suggestions."""
        suggestions = []

        if readiness_score < self.SCORE_GOOD:
            # Increase savings rate
            current_rate = (profile.monthly_savings or 0) / profile.monthly_income if profile.monthly_income > 0 else 0
            if current_rate < 0.15:
                suggestions.append(
                    f"考慮將儲蓄率提高到收入的15-20%，"
                    f"每月多儲蓄約NT${int((0.15 - current_rate) * profile.monthly_income):,}。"
                )

        if years_to_retirement > 10:
            # Maximize tax-advantaged accounts
            suggestions.append("最大化使用勞退自提和政府稅優惠帳戶。")

        if not profile.has_emergency_fund:
            suggestions.append("先建立3-6個月緊急備用金再增加退休儲蓄。")

        if profile.risk_tolerance == "conservative" and years_to_retirement > 15:
            suggestions.append("年輕時可考慮適度增加投資風險承受度，提高成長型資產比例。")

        if monthly_contribution_needed > profile.monthly_income * 0.3:
            suggestions.append(
                "退休目標可能過於激進，考慮調整退休生活預期或延長工作年限。"
            )

        if profile.passive_income_monthly and profile.passive_income_monthly < annual_expenses_needed * 0.3:
            suggestions.append("考虑增加被動收入來源，如股息、租金收入等。")

        # Diversification suggestion
        suggestions.append("定期檢視投資組合，確保資產配置符合年齡和風險偏好。")

        return suggestions

    def _calculate_confidence(
        self,
        profile: PersonalFinancialProfile,
        years_to_retirement: int,
    ) -> float:
        """Calculate confidence in the assessment."""
        confidence = 0.7  # Base confidence

        # More factors known = higher confidence
        if profile.monthly_savings is not None:
            confidence += 0.1
        if profile.passive_income_monthly is not None:
            confidence += 0.05
        if profile.total_debt is not None:
            confidence += 0.05
        if profile.has_emergency_fund:
            confidence += 0.05

        # Time in market = higher confidence
        if years_to_retirement > 20:
            confidence += 0.05

        return min(confidence, 0.95)


# Helper for backwards compatibility
def calculate_retirement_readiness(
    profile: PersonalFinancialProfile,
    current_savings: float,
    annual_expenses: float,
    retirement_age: int = 65,
) -> RetirementReadinessResult:
    """Synchronous wrapper for quick assessments."""
    service = RetirementReadinessService()
    return service.assess_retirement_readiness(
        profile=profile,
        current_savings=current_savings,
        annual_expenses=annual_expenses,
        retirement_age=retirement_age,
    )

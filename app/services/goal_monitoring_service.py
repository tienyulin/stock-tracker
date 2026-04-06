"""
Goal-Based Portfolio Monitoring Service

Tracks user financial goals (retirement, house, education) and monitors
progress against targets. Integrates with Monte Carlo simulations for
retirement gap calculation and triggers alerts when goals are at risk.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from app.schemas.agent_schemas import (
    GoalDefinition,
    GoalProgress,
    GoalStatus,
    GoalType,
    MonitoringAlert,
    PersonalFinancialProfile,
    RetirementGapResult,
)
from app.schemas.schemas import RetirementSimulationRequest
from app.services.monte_carlo_service import MonteCarloService


@dataclass
class GoalMonitoringConfig:
    """Configuration for goal monitoring thresholds and behavior."""

    # Alert thresholds (as percentage of target)
    warning_threshold: float = 0.80  # Alert when 80% of time elapsed but < 80% progress
    critical_threshold: float = 0.90  # Critical when 90% of time elapsed
    min_goal_progress_per_month: float = 0.005  # Minimum 0.5% progress per month

    # Retirement-specific settings
    retirement_success_probability_min: float = 0.80  # Minimum 80% success rate
    retirement_safe_withdrawal_rate: float = 0.04  # 4% rule

    # Alert cooldown (hours) to prevent spam
    alert_cooldown_hours: int = 24


class GoalMonitoringService:
    """Service for monitoring and analyzing progress toward financial goals."""

    def __init__(self, config: Optional[GoalMonitoringConfig] = None):
        """Initialize Goal Monitoring Service.

        Args:
            config: Optional custom configuration.
        """
        self.config = config or GoalMonitoringConfig()
        self._monte_carlo = MonteCarloService()

    async def check_goal_progress(
        self,
        goal: GoalDefinition,
        profile: PersonalFinancialProfile,
    ) -> GoalProgress:
        """Calculate progress toward a specific goal.

        Args:
            goal: The goal definition.
            profile: User's current financial profile.

        Returns:
            GoalProgress with current status and projections.
        """
        now = datetime.now()
        today = date.today()

        current_amount = goal.current_amount
        target_amount = goal.target_amount
        progress_percent = min(100.0, (current_amount / target_amount * 100)) if target_amount > 0 else 0

        # Calculate monthly contribution from profile
        monthly_actual = self._calculate_monthly_contribution(profile, goal)
        monthly_needed = self._calculate_required_monthly(target_amount, current_amount, goal, today)

        # Determine if on track
        on_track = self._is_on_track(goal, progress_percent, today)

        # Determine status
        status = self._determine_status(goal, progress_percent, on_track, today)

        # Calculate projected completion
        projected_completion = self._project_completion_date(
            current_amount, target_amount, monthly_actual, goal, today
        )

        # Calculate gap
        gap_amount = max(0, target_amount - current_amount)

        # Generate alerts
        alerts = self._generate_alerts(goal, progress_percent, on_track, status, today)

        return GoalProgress(
            goal_id=goal.id,
            goal_name=goal.name,
            goal_type=goal.goal_type,
            target_amount=target_amount,
            current_amount=current_amount,
            target_date=goal.target_date,
            progress_percent=round(progress_percent, 2),
            monthly_needed=round(monthly_needed, 2),
            monthly_actual=round(monthly_actual, 2),
            on_track=on_track,
            status=status,
            projected_completion=projected_completion,
            gap_amount=round(gap_amount, 2),
            alerts=alerts,
            timestamp=now,
        )

    def calculate_retirement_gap(
        self,
        goal: GoalDefinition,
        profile: PersonalFinancialProfile,
        current_age: int,
        retirement_age: int,
    ) -> RetirementGapResult:
        """Calculate retirement gap using Monte Carlo simulation.

        Args:
            goal: The retirement goal definition.
            profile: User's financial profile.
            current_age: User's current age.
            retirement_age: Target retirement age.

        Returns:
            RetirementGapResult with gap analysis.
        """
        if goal.goal_type != GoalType.RETIREMENT:
            raise ValueError("Retirement gap calculation only valid for RETIREMENT goals")

        current_savings = goal.current_amount
        monthly_contribution = goal.monthly_contribution or self._calculate_monthly_contribution(
            profile, goal
        )

        # Calculate required retirement nest egg
        # Using 25x rule (inverse of 4% safe withdrawal rate)
        desired_annual = self._estimate_annual_retirement_needs(profile)
        required_at_retirement = desired_annual * 25

        # Build portfolio allocation from profile
        portfolio_allocation = self._build_portfolio_allocation(profile)

        # Run Monte Carlo simulation
        request = RetirementSimulationRequest(
            current_age=current_age,
            retirement_age=retirement_age,
            current_savings=current_savings,
            monthly_contribution=monthly_contribution,
            desired_monthly_income=desired_annual / 12,
            portfolio_allocation=portfolio_allocation,
            num_simulations=1000,
        )

        simulation = self._monte_carlo.run_retirement_simulation(request)

        # Calculate gap
        gap_amount = max(0, required_at_retirement - simulation.median_outcome)
        gap_percentage = (gap_amount / required_at_retirement * 100) if required_at_retirement > 0 else 0

        # Monthly shortfall/surplus
        years_to_retirement = retirement_age - current_age
        if years_to_retirement > 0:
            total_future_contributions = monthly_contribution * 12 * years_to_retirement
            needed_from_growth = gap_amount - total_future_contributions
            monthly_shortfall = max(0, needed_from_growth / (years_to_retirement * 12))
            monthly_surplus = max(
                0,
                abs(needed_from_growth) / (years_to_retirement * 12)
                if needed_from_growth < 0
                else 0,
            )
        else:
            monthly_shortfall = 0
            monthly_surplus = 0

        return RetirementGapResult(
            current_savings=current_savings,
            required_at_retirement=required_at_retirement,
            gap_amount=round(gap_amount, 2),
            gap_percentage=round(gap_percentage, 2),
            success_probability=simulation.success_probability,
            monthly_shortfall=round(monthly_shortfall, 2),
            monthly_surplus=round(monthly_surplus, 2),
            years_to_retirement=years_to_retirement,
            recommended_monthly_contribution=round(
                self._calculate_required_monthly(
                    required_at_retirement, current_savings, goal, date.today()
                ),
                2,
            ),
            assumptions={
                "safe_withdrawal_rate": self.config.retirement_safe_withdrawal_rate,
                "desired_annual_income": desired_annual,
                "median_simulation_outcome": simulation.median_outcome,
                "simulation_percentile_10": simulation.percentile_10,
                "simulation_percentile_90": simulation.percentile_90,
            },
            simulated_at=datetime.now(),
        )

    def generate_monitoring_alerts(
        self,
        goal: GoalDefinition,
        progress: GoalProgress,
    ) -> list[MonitoringAlert]:
        """Generate monitoring alerts based on goal status.

        Args:
            goal: The goal definition.
            progress: Current goal progress.

        Returns:
            List of MonitoringAlert objects.
        """
        alerts: list[MonitoringAlert] = []
        now = datetime.now()

        if progress.status == GoalStatus.BEHIND:
            alerts.append(
                MonitoringAlert(
                    alert_id=UUID,
                    goal_id=goal.id,
                    alert_type="GOAL_OFF_TRACK",
                    severity="WARNING",
                    title=f"Goal '{goal.name}' is behind schedule",
                    message=f"You're {progress.gap_amount:.0f} {progress.gap_amount} behind target. "
                    f"Consider increasing monthly contributions.",
                    recommendation=f"Increase monthly contribution from {progress.monthly_actual:.0f} "
                    f"to {progress.monthly_needed:.0f} to get back on track.",
                    created_at=now,
                )
            )

        elif progress.status == GoalStatus.AT_RISK:
            alerts.append(
                MonitoringAlert(
                    alert_id=UUID,
                    goal_id=goal.id,
                    alert_type="GOAL_OFF_TRACK",
                    severity="CRITICAL",
                    title=f"Goal '{goal.name}' is at risk",
                    message=f"You're significantly behind with only {progress.progress_percent:.1f}% "
                    f"of target achieved.",
                    recommendation=f"Urgently review and increase contributions or adjust the target.",
                    created_at=now,
                )
            )

        # Check for opportunity: goal will be achieved early
        if progress.projected_completion and progress.projected_completion < (goal.target_date or date.max):
            alerts.append(
                MonitoringAlert(
                    alert_id=UUID,
                    goal_id=goal.id,
                    alert_type="OPPORTUNITY",
                    severity="INFO",
                    title=f"Goal '{goal.name}' ahead of schedule",
                    message=f"Projected completion: {progress.projected_completion}. "
                    f"Target date: {goal.target_date}",
                    recommendation="Consider increasing your target or reallocating savings to other goals.",
                    created_at=now,
                )
            )

        # Retirement-specific: success probability check
        if goal.goal_type == GoalType.RETIREMENT:
            # Run a quick retirement gap check
            if progress.progress_percent < 50 and (goal.target_date or date.max):
                days_remaining = (goal.target_date - date.today()).days if goal.target_date else 365
                if days_remaining < 3650:  # Less than 10 years
                    alerts.append(
                        MonitoringAlert(
                            alert_id=UUID,
                            goal_id=goal.id,
                            alert_type="RISK",
                            severity="CRITICAL",
                            title="Retirement planning may be insufficient",
                            message=f"Only {progress.progress_percent:.1f}% of retirement goal funded "
                            f"with < 10 years remaining.",
                            recommendation="Maximize contributions and consider adjusting retirement timeline.",
                            created_at=now,
                        )
                    )

        return alerts

    def _calculate_monthly_contribution(
        self,
        profile: PersonalFinancialProfile,
        goal: GoalDefinition,
    ) -> float:
        """Calculate average monthly contribution toward a goal.

        Args:
            profile: User's financial profile.
            goal: The goal being tracked.

        Returns:
            Estimated monthly contribution amount.
        """
        # Use goal's declared monthly contribution if available
        if goal.monthly_contribution > 0:
            return goal.monthly_contribution

        # Estimate from income and savings rate
        monthly_savings = (profile.monthly_income - profile.monthly_expenses) * 0.3  # Assume 30% goes to goals
        return max(0, monthly_savings)

    def _calculate_required_monthly(
        self,
        target: float,
        current: float,
        goal: GoalDefinition,
        today: date,
    ) -> float:
        """Calculate required monthly contribution to meet goal.

        Args:
            target: Target amount.
            current: Current amount saved.
            goal: Goal definition with target date.
            today: Today's date.

        Returns:
            Required monthly contribution.
        """
        if current >= target:
            return 0

        remaining = target - current

        if goal.target_date:
            months_remaining = max(1, (goal.target_date.year - today.year) * 12 + (goal.target_date.month - today.month))
            return remaining / months_remaining

        # No target date: assume 10 years
        return remaining / 120

    def _is_on_track(
        self,
        goal: GoalDefinition,
        progress_percent: float,
        today: date,
    ) -> bool:
        """Determine if goal is on track based on time elapsed.

        Args:
            goal: The goal definition.
            progress_percent: Current progress percentage.
            today: Today's date.

        Returns:
            True if on track.
        """
        if not goal.target_date:
            # No deadline, consider on track if > 50% saved
            return progress_percent >= 50

        total_days = (goal.target_date - today).days if today < goal.target_date else 1
        elapsed_days = (date.today() - goal.created_at.date()).days if goal.created_at else 0
        time_elapsed = elapsed_days / max(1, total_days + elapsed_days)

        # On track if progress >= time elapsed
        return progress_percent >= (time_elapsed * 100)

    def _determine_status(
        self,
        goal: GoalDefinition,
        progress_percent: float,
        on_track: bool,
        today: date,
    ) -> GoalStatus:
        """Determine goal status.

        Args:
            goal: The goal definition.
            progress_percent: Current progress percentage.
            on_track: Whether goal is on track.
            today: Today's date.

        Returns:
            GoalStatus enum value.
        """
        if goal.current_amount >= goal.target_amount:
            return GoalStatus.ACHIEVED

        if goal.status == GoalStatus.CANCELLED:
            return GoalStatus.CANCELLED

        if not on_track:
            # Check how far behind
            if progress_percent < 50:
                return GoalStatus.BEHHIND
            return GoalStatus.AT_RISK

        return GoalStatus.ON_TRACK

    def _project_completion_date(
        self,
        current: float,
        target: float,
        monthly: float,
        goal: GoalDefinition,
        today: date,
    ) -> Optional[date]:
        """Project when a goal will be achieved.

        Args:
            current: Current amount.
            target: Target amount.
            monthly: Monthly contribution rate.
            goal: Goal definition.
            today: Today's date.

        Returns:
            Projected completion date, or None if cannot project.
        """
        if current >= target:
            return today

        if monthly <= 0:
            return None

        remaining = target - current
        months_needed = remaining / monthly

        # Cap at 50 years
        if months_needed > 600:
            return None

        from dateutil.relativedelta import relativedelta

        return today + relativedelta(months=int(months_needed))

    def _estimate_annual_retirement_needs(self, profile: PersonalFinancialProfile) -> float:
        """Estimate annual retirement income needs based on profile.

        Args:
            profile: User's financial profile.

        Returns:
            Estimated annual retirement income needed.
        """
        # Use 70% of current expenses as baseline (retirement spending typically lower)
        annual_expenses = profile.monthly_expenses * 12
        baseline = annual_expenses * 0.70

        # Ensure minimum based on current lifestyle
        min_needed = profile.monthly_income * 12 * 0.60

        return max(baseline, min_needed)

    def _build_portfolio_allocation(self, profile: PersonalFinancialProfile) -> dict[str, float]:
        """Build portfolio allocation from financial profile.

        Args:
            profile: User's financial profile.

        Returns:
            Asset allocation dict.
        """
        # Default allocation based on investment amount
        if profile.total_investments <= 0:
            return {"stocks": 0.7, "bonds": 0.2, "cash": 0.1}

        # Build from holdings if available
        if profile.holdings:
            total = sum(h.current_value for h in profile.holdings)
            if total > 0:
                stocks = sum(h.current_value for h in profile.holdings if h.asset_class == "stock") / total
                bonds = sum(h.current_value for h in profile.holdings if h.asset_class == "bond") / total
                cash = sum(h.current_value for h in profile.holdings if h.asset_class == "cash") / total

                # Normalize to sum to 1
                total_alloc = stocks + bonds + cash
                if total_alloc > 0:
                    return {
                        "stocks": stocks / total_alloc,
                        "bonds": bonds / total_alloc,
                        "cash": cash / total_alloc,
                    }

        return {"stocks": 0.7, "bonds": 0.2, "cash": 0.1}

    def _generate_alerts(
        self,
        goal: GoalDefinition,
        progress_percent: float,
        on_track: bool,
        status: GoalStatus,
        today: date,
    ) -> list[str]:
        """Generate alert messages for goal status.

        Args:
            goal: The goal definition.
            progress_percent: Current progress percentage.
            on_track: Whether goal is on track.
            status: Goal status.
            today: Today's date.

        Returns:
            List of alert message strings.
        """
        alerts: list[str] = []

        if status == GoalStatus.AT_RISK:
            alerts.append(
                f"⚠️ Goal '{goal.name}' is at risk of not meeting the target date. "
                f"Current progress: {progress_percent:.1f}%"
            )
        elif status == GoalStatus.BEHIND:
            alerts.append(
                f"🔴 Goal '{goal.name}' is behind schedule. "
                f"Current progress: {progress_percent:.1f}%"
            )
        elif status == GoalStatus.ON_TRACK:
            alerts.append(
                f"✅ Goal '{goal.name}' is on track. "
                f"Current progress: {progress_percent:.1f}%"
            )

        return alerts

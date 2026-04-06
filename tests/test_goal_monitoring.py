"""
Tests for Goal Monitoring Service
"""

import pytest
from datetime import date, datetime
from uuid import uuid4

from app.schemas.agent_schemas import (
    GoalDefinition,
    GoalProgress,
    GoalStatus,
    GoalType,
    PersonalFinancialProfile,
    HoldingAsset,
    AccountBalance,
    OpenFinanceProvider,
)
from app.services.goal_monitoring_service import (
    GoalMonitoringService,
    GoalMonitoringConfig,
)


class TestGoalMonitoringConfig:
    """Tests for GoalMonitoringConfig defaults."""

    def test_default_config_values(self):
        """Should have sensible default values."""
        config = GoalMonitoringConfig()
        assert config.warning_threshold == 0.80
        assert config.critical_threshold == 0.90
        assert config.retirement_success_probability_min == 0.80
        assert config.retirement_safe_withdrawal_rate == 0.04
        assert config.alert_cooldown_hours == 24

    def test_custom_config(self):
        """Should accept custom configuration."""
        config = GoalMonitoringConfig(
            warning_threshold=0.70,
            critical_threshold=0.85,
            retirement_success_probability_min=0.90,
        )
        assert config.warning_threshold == 0.70
        assert config.critical_threshold == 0.85
        assert config.retirement_success_probability_min == 0.90


class TestGoalMonitoringService:
    """Tests for GoalMonitoringService."""

    @pytest.fixture
    def service(self):
        """Create a goal monitoring service with defaults."""
        return GoalMonitoringService()

    @pytest.fixture
    def sample_profile(self):
        """Create a sample financial profile."""
        return PersonalFinancialProfile(
            user_id=uuid4(),
            monthly_income=100000,
            monthly_expenses=60000,
            total_investments=500000,
            total_cash=100000,
            total_assets=600000,
            total_liabilities=0,
            last_updated=datetime.now(),
        )

    @pytest.fixture
    def retirement_goal(self):
        """Create a retirement goal."""
        return GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Retirement Fund",
            goal_type=GoalType.RETIREMENT,
            target_amount=10_000_000,
            current_amount=5_000_000,
            monthly_contribution=50000,
            target_date=date(2035, 1, 1),
            status=GoalStatus.ON_TRACK,
            priority=1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )


class TestCheckGoalProgress(TestGoalMonitoringService):
    """Tests for goal progress checking."""

    @pytest.fixture
    def service(self):
        """Create a goal monitoring service with defaults."""
        return GoalMonitoringService()

    @pytest.fixture
    def sample_profile(self):
        """Create a sample financial profile."""
        return PersonalFinancialProfile(
            user_id=uuid4(),
            monthly_income=100000,
            monthly_expenses=60000,
            total_investments=500000,
            total_cash=100000,
            total_assets=600000,
            total_liabilities=0,
            last_updated=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_progress_on_track_goal(self, service, sample_profile):
        """Goal with 50% progress at 50% time elapsed should be on track."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="House Down Payment",
            goal_type=GoalType.HOUSE,
            target_amount=5_000_000,
            current_amount=2_500_000,  # 50%
            monthly_contribution=100000,
            target_date=date(2030, 1, 1),  # 4 years away
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        progress = await service.check_goal_progress(goal, sample_profile)

        assert progress.progress_percent == 50.0
        assert progress.on_track is True
        assert progress.status == GoalStatus.ON_TRACK
        assert progress.gap_amount == 2_500_000

    @pytest.mark.asyncio
    async def test_progress_behind_goal(self, service, sample_profile):
        """Goal with low progress at deadline should be behind."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Emergency Fund",
            goal_type=GoalType.EMERGENCY_FUND,
            target_amount=300000,
            current_amount=50000,  # Only 16.7%
            monthly_contribution=5000,
            target_date=date.today(),  # Due today
            created_at=datetime(2020, 1, 1),  # Created long ago
            updated_at=datetime.now(),
        )

        progress = await service.check_goal_progress(goal, sample_profile)

        assert progress.progress_percent == pytest.approx(16.67, rel=0.1)
        assert progress.on_track is False
        assert progress.status == GoalStatus.BEHIND
        assert len(progress.alerts) > 0

    @pytest.mark.asyncio
    async def test_progress_achieved_goal(self, service, sample_profile):
        """Goal that's been fully achieved."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Paid Off Car",
            goal_type=GoalType.CUSTOM,
            target_amount=500000,
            current_amount=600000,  # Exceeded
            monthly_contribution=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        progress = await service.check_goal_progress(goal, sample_profile)

        assert progress.progress_percent == 100.0
        assert progress.status == GoalStatus.ACHIEVED
        assert progress.gap_amount == 0

    @pytest.mark.asyncio
    async def test_monthly_contribution_from_goal(self, service, sample_profile):
        """Should use goal's monthly contribution when available."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Vacation Fund",
            goal_type=GoalType.CUSTOM,
            target_amount=200000,
            current_amount=50000,
            monthly_contribution=25000,  # Explicit
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        progress = await service.check_goal_progress(goal, sample_profile)

        assert progress.monthly_actual == 25000

    @pytest.mark.asyncio
    async def test_monthly_contribution_estimated(self, service, sample_profile):
        """Should estimate monthly contribution when not specified."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="General Savings",
            goal_type=GoalType.WEALTH_ACCUMULATION,
            target_amount=1_000_000,
            current_amount=0,
            monthly_contribution=0,  # Not specified
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        progress = await service.check_goal_progress(goal, sample_profile)

        # Should estimate from income - expenses
        expected_monthly = (sample_profile.monthly_income - sample_profile.monthly_expenses) * 0.3
        assert progress.monthly_actual == expected_monthly


class TestCalculateRetirementGap(TestGoalMonitoringService):
    """Tests for retirement gap calculation."""

    @pytest.mark.asyncio
    async def test_retirement_gap_calculation(self, service, sample_profile):
        """Should calculate retirement gap with Monte Carlo."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Retirement",
            goal_type=GoalType.RETIREMENT,
            target_amount=10_000_000,
            current_amount=3_000_000,
            monthly_contribution=30000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = await service.calculate_retirement_gap(
            goal=goal,
            profile=sample_profile,
            current_age=35,
            retirement_age=60,
        )

        assert result.current_savings == 3_000_000
        assert result.years_to_retirement == 25
        assert 0.0 <= result.success_probability <= 1.0
        assert result.gap_amount >= 0
        assert "safe_withdrawal_rate" in result.assumptions

    @pytest.mark.asyncio
    async def test_retirement_gap_non_retirement_goal_raises(self, service, sample_profile):
        """Should raise ValueError for non-retirement goals."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="House",
            goal_type=GoalType.HOUSE,
            target_amount=5_000_000,
            current_amount=1_000_000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with pytest.raises(ValueError, match="RETIREMENT goals only"):
            await service.calculate_retirement_gap(
                goal=goal,
                profile=sample_profile,
                current_age=30,
                retirement_age=65,
            )

    @pytest.mark.asyncio
    async def test_retirement_gap_high_contributions_success(self, service, sample_profile):
        """High contributions should lead to higher success probability."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Early Retirement",
            goal_type=GoalType.RETIREMENT,
            target_amount=10_000_000,
            current_amount=8_000_000,  # 80% funded
            monthly_contribution=100000,  # High
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        result = await service.calculate_retirement_gap(
            goal=goal,
            profile=sample_profile,
            current_age=45,
            retirement_age=55,  # 10 years
        )

        # Should have reasonable success probability with high funding
        assert result.success_probability > 0.5


class TestGenerateMonitoringAlerts(TestGoalMonitoringService):
    """Tests for monitoring alert generation."""

    @pytest.fixture
    def service(self):
        """Create a goal monitoring service with defaults."""
        return GoalMonitoringService()

    def test_alert_behind_goal(self, service):
        """Should generate warning for behind goal."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Education Fund",
            goal_type=GoalType.EDUCATION,
            target_amount=1_000_000,
            current_amount=200000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        progress = GoalProgress(
            goal_id=goal.id,
            goal_name=goal.name,
            goal_type=goal.goal_type,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            target_date=date(2026, 9, 1),  # Soon
            progress_percent=20.0,
            monthly_needed=100000,
            monthly_actual=10000,
            on_track=False,
            status=GoalStatus.BEHIND,
            gap_amount=800000,
            alerts=[],
            timestamp=datetime.now(),
        )

        alerts = service.generate_monitoring_alerts(goal, progress)

        assert len(alerts) >= 1
        warning_alert = next((a for a in alerts if a.severity == "WARNING"), None)
        assert warning_alert is not None
        assert "behind" in warning_alert.title.lower()

    def test_alert_at_risk_goal(self, service):
        """Should generate critical alert for at-risk goal."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Retirement",
            goal_type=GoalType.RETIREMENT,
            target_amount=10_000_000,
            current_amount=4_000_000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        progress = GoalProgress(
            goal_id=goal.id,
            goal_name=goal.name,
            goal_type=goal.goal_type,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            target_date=date(2027, 1, 1),
            progress_percent=40.0,
            monthly_needed=200000,
            monthly_actual=50000,
            on_track=False,
            status=GoalStatus.AT_RISK,
            gap_amount=6_000_000,
            alerts=[],
            timestamp=datetime.now(),
        )

        alerts = service.generate_monitoring_alerts(goal, progress)

        critical_alert = next((a for a in alerts if a.severity == "CRITICAL"), None)
        assert critical_alert is not None

    def test_alert_ahead_of_schedule(self, service):
        """Should generate info alert when ahead of schedule."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="House Fund",
            goal_type=GoalType.HOUSE,
            target_amount=5_000_000,
            current_amount=4_000_000,
            target_date=date(2030, 1, 1),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        progress = GoalProgress(
            goal_id=goal.id,
            goal_name=goal.name,
            goal_type=goal.goal_type,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            target_date=date(2030, 1, 1),
            progress_percent=80.0,
            monthly_needed=20000,
            monthly_actual=50000,
            on_track=True,
            status=GoalStatus.ON_TRACK,
            projected_completion=date(2027, 6, 1),  # Way ahead
            gap_amount=0,
            alerts=[],
            timestamp=datetime.now(),
        )

        alerts = service.generate_monitoring_alerts(goal, progress)

        info_alert = next((a for a in alerts if a.alert_type == "OPPORTUNITY"), None)
        assert info_alert is not None


class TestInternalHelpers(TestGoalMonitoringService):
    """Tests for internal helper methods."""

    @pytest.fixture
    def service(self):
        """Create a goal monitoring service."""
        return GoalMonitoringService()

    def test_calculate_monthly_from_goal(self, service, sample_profile):
        """Should return goal's monthly contribution when set."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            goal_type=GoalType.CUSTOM,
            target_amount=100000,
            current_amount=0,
            monthly_contribution=5000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        monthly = service._calculate_monthly_contribution(sample_profile, goal)
        assert monthly == 5000

    def test_calculate_monthly_estimated(self, service, sample_profile):
        """Should estimate monthly contribution when not set."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            goal_type=GoalType.CUSTOM,
            target_amount=100000,
            current_amount=0,
            monthly_contribution=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        monthly = service._calculate_monthly_contribution(sample_profile, goal)

        # Should be 30% of savings (income - expenses)
        expected = (sample_profile.monthly_income - sample_profile.monthly_expenses) * 0.3
        assert monthly == expected

    def test_is_on_track_no_deadline(self, service):
        """Should consider on track if > 50% saved with no deadline."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            goal_type=GoalType.WEALTH_ACCUMULATION,
            target_amount=100000,
            current_amount=60000,  # 60%
            target_date=None,  # No deadline
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        on_track = service._is_on_track(goal, 60.0, date.today())
        assert on_track is True

    def test_is_on_track_with_time_elapsed(self, service):
        """Should compare progress to time elapsed."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            goal_type=GoalType.HOUSE,
            target_amount=5_000_000,
            current_amount=2_500_000,  # 50%
            target_date=date(2030, 1, 1),
            created_at=datetime(2024, 1, 1),  # 1 year ago
            updated_at=datetime.now(),
        )

        # About 50% of time elapsed, 50% progress = on track
        on_track = service._is_on_track(goal, 50.0, date(2025, 1, 1))
        assert on_track is True

    def test_estimate_annual_retirement_needs(self, service, sample_profile):
        """Should estimate annual retirement income needs."""
        needs = service._estimate_annual_retirement_needs(sample_profile)

        # Should be 70% of expenses OR 60% of income, whichever is higher
        from_expenses = sample_profile.monthly_expenses * 12 * 0.70
        from_income = sample_profile.monthly_income * 12 * 0.60

        assert needs >= from_income
        assert needs == max(from_expenses, from_income)

    def test_build_portfolio_allocation_default(self, service, sample_profile):
        """Should return default allocation when no holdings."""
        allocation = service._build_portfolio_allocation(sample_profile)

        assert "stocks" in allocation
        assert "bonds" in allocation
        assert "cash" in allocation
        assert abs(sum(allocation.values()) - 1.0) < 0.001

    def test_build_portfolio_allocation_from_holdings(self, service, sample_profile):
        """Should build allocation from actual holdings."""
        sample_profile.holdings = [
            HoldingAsset(symbol="AAPL", current_value=70000, asset_class="stock"),
            HoldingAsset(symbol="BND", current_value=20000, asset_class="bond"),
            HoldingAsset(symbol="CASH", current_value=10000, asset_class="cash"),
        ]

        allocation = service._build_portfolio_allocation(sample_profile)

        assert allocation["stocks"] == pytest.approx(0.7, rel=0.01)
        assert allocation["bonds"] == pytest.approx(0.2, rel=0.01)
        assert allocation["cash"] == pytest.approx(0.1, rel=0.01)

    def test_project_completion_date(self, service):
        """Should project goal completion date."""
        today = date.today()

        # Project: need 120000 more, saving 10000/month = 12 months
        completion = service._project_completion_date(
            current=30000,
            target=150000,
            monthly=10000,
            goal=GoalDefinition(
                id=uuid4(),
                user_id=uuid4(),
                name="Test",
                goal_type=GoalType.CUSTOM,
                target_amount=150000,
                current_amount=30000,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            today=today,
        )

        from dateutil.relativedelta import relativedelta

        expected = today + relativedelta(months=12)
        assert completion == expected

    def test_project_completion_already_met(self, service):
        """Should return today if goal already met."""
        completion = service._project_completion_date(
            current=100000,
            target=80000,
            monthly=0,
            goal=GoalDefinition(
                id=uuid4(),
                user_id=uuid4(),
                name="Test",
                goal_type=GoalType.CUSTOM,
                target_amount=80000,
                current_amount=100000,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            today=date.today(),
        )

        assert completion == date.today()

    def test_project_completion_zero_monthly(self, service):
        """Should return None if monthly contribution is zero."""
        completion = service._project_completion_date(
            current=10000,
            target=100000,
            monthly=0,
            goal=GoalDefinition(
                id=uuid4(),
                user_id=uuid4(),
                name="Test",
                goal_type=GoalType.CUSTOM,
                target_amount=100000,
                current_amount=10000,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            today=date.today(),
        )

        assert completion is None


class TestGoalStatusDetermination(TestGoalMonitoringService):
    """Tests for goal status determination."""

    @pytest.fixture
    def service(self):
        """Create a goal monitoring service."""
        return GoalMonitoringService()

    def test_determine_status_achieved(self, service):
        """Should return ACHIEVED when current >= target."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            goal_type=GoalType.CUSTOM,
            target_amount=100000,
            current_amount=150000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        status = service._determine_status(goal, 150.0, True, date.today())
        assert status == GoalStatus.ACHIEVED

    def test_determine_status_on_track(self, service):
        """Should return ON_TRACK when on track."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            goal_type=GoalType.CUSTOM,
            target_amount=100000,
            current_amount=60000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        status = service._determine_status(goal, 60.0, True, date.today())
        assert status == GoalStatus.ON_TRACK

    def test_determine_status_at_risk(self, service):
        """Should return AT_RISK when behind but not too far."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            goal_type=GoalType.CUSTOM,
            target_amount=100000,
            current_amount=30000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        status = service._determine_status(goal, 30.0, False, date.today())
        assert status == GoalStatus.AT_RISK

    def test_determine_status_behind(self, service):
        """Should return BEHIND when significantly behind."""
        goal = GoalDefinition(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            goal_type=GoalType.CUSTOM,
            target_amount=100000,
            current_amount=20000,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        status = service._determine_status(goal, 20.0, False, date.today())
        assert status == GoalStatus.BEHIND

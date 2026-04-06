"""
Tests for AI Agent Orchestration Service
"""

import pytest
from datetime import date, datetime
from uuid import uuid4

from app.schemas.agent_schemas import (
    AgentState,
    GoalDefinition,
    GoalType,
    GoalStatus,
    PersonalFinancialProfile,
    HoldingAsset,
    AccountBalance,
    OpenFinanceProvider,
)
from app.services.agent_orchestration_service import (
    AgentOrchestrationService,
    AgentEvent,
    OrchestrationContext,
    Tool,
)


class TestAgentStateMachine:
    """Tests for FSM state transitions."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return AgentOrchestrationService()

    def test_initial_state_is_idle(self, service):
        """Service should start in IDLE state."""
        assert service.state == AgentState.IDLE

    def test_idle_to_monitoring_transition(self, service):
        """IDLE + START_MONITORING -> MONITORING."""
        next_state = service.transition(AgentEvent.START_MONITORING)
        assert next_state == AgentState.MONITORING
        assert service.state == AgentState.MONITORING

    def test_monitoring_to_idle_transition(self, service):
        """MONITORING + STOP_MONITORING -> IDLE."""
        service.transition(AgentEvent.START_MONITORING)
        next_state = service.transition(AgentEvent.STOP_MONITORING)
        assert next_state == AgentState.IDLE

    def test_idle_to_analyzing_transition(self, service):
        """IDLE + ANALYZE_NOW -> ANALYZING."""
        next_state = service.transition(AgentEvent.ANALYZE_NOW)
        assert next_state == AgentState.ANALYZING

    def test_analyzing_to_recommending_transition(self, service):
        """ANALYZING + RECOMMEND -> RECOMMENDING."""
        service.transition(AgentEvent.ANALYZE_NOW)
        next_state = service.transition(AgentEvent.RECOMMEND)
        assert next_state == AgentState.RECOMMENDING

    def test_recommending_to_acting_transition(self, service):
        """RECOMMENDING + TAKE_ACTION -> ACTING."""
        service.transition(AgentEvent.ANALYZE_NOW)
        service.transition(AgentEvent.RECOMMEND)
        next_state = service.transition(AgentEvent.TAKE_ACTION)
        assert next_state == AgentState.ACTING

    def test_acting_to_idle_transition(self, service):
        """ACTING + ACTION_COMPLETE -> IDLE."""
        service.transition(AgentEvent.ANALYZE_NOW)
        service.transition(AgentEvent.RECOMMEND)
        service.transition(AgentEvent.TAKE_ACTION)
        next_state = service.transition(AgentEvent.ACTION_COMPLETE)
        assert next_state == AgentState.IDLE

    def test_invalid_transition_raises_error(self, service):
        """Invalid transition should raise ValueError."""
        service.transition(AgentEvent.START_MONITORING)
        with pytest.raises(ValueError, match="Invalid transition"):
            service.transition(AgentEvent.RECOMMEND)  # Can't RECOMMEND from MONITORING

    def test_error_transition_from_monitoring(self, service):
        """MONITORING + ERROR -> IDLE."""
        service.transition(AgentEvent.START_MONITORING)
        next_state = service.transition(AgentEvent.ERROR)
        assert next_state == AgentState.IDLE


class TestOrchestrationContext:
    """Tests for OrchestrationContext."""

    def test_create_context(self):
        """Context should be created with user_id."""
        ctx = OrchestrationContext(user_id="user123")
        assert ctx.user_id == "user123"
        assert ctx.profile is None
        assert ctx.goals == []
        assert ctx.monitoring_active is False

    def test_context_with_profile(self):
        """Context can hold a financial profile."""
        profile = PersonalFinancialProfile(
            user_id=uuid4(),
            total_net_worth=100000,
            total_assets=120000,
            total_liabilities=20000,
            last_updated=datetime.now(),
        )
        ctx = OrchestrationContext(user_id="user123", profile=profile)
        assert ctx.profile.total_net_worth == 100000


class TestAgentTools:
    """Tests for LangChain-style tool registry."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return AgentOrchestrationService()

    def test_list_tools(self, service):
        """Should return a list of tool definitions."""
        tools = service.list_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Each tool should have required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool

    def test_get_tool_by_name(self, service):
        """Should retrieve a tool by name."""
        tool = service.get_tool("analyze_portfolio_drift")
        assert tool is not None
        assert isinstance(tool, Tool)
        assert tool.name == "analyze_portfolio_drift"

    def test_get_nonexistent_tool(self, service):
        """Should return None for unknown tool."""
        tool = service.get_tool("nonexistent_tool")
        assert tool is None

    def test_available_tools_in_idle_state(self, service):
        """No tools should be available in IDLE state."""
        tools = service.get_available_tools()
        assert tools == []

    def test_available_tools_in_monitoring_state(self, service):
        """Tools should be available in MONITORING state."""
        service.transition(AgentEvent.START_MONITORING)
        tools = service.get_available_tools()
        assert len(tools) > 0


class TestContextManagement:
    """Tests for user context management."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return AgentOrchestrationService()

    def test_get_or_create_context_new_user(self, service):
        """Should create new context for new user."""
        ctx = service.get_or_create_context("new_user")
        assert ctx.user_id == "new_user"
        assert ctx.monitoring_active is False

    def test_get_or_create_context_existing_user(self, service):
        """Should return existing context for known user."""
        ctx1 = service.get_or_create_context("existing_user")
        ctx1.monitoring_active = True

        ctx2 = service.get_or_create_context("existing_user")
        assert ctx2.monitoring_active is True
        assert ctx1 is ctx2  # Same object

    def test_clear_context(self, service):
        """Should clear context for a user."""
        # Create initial context
        service.get_or_create_context("user_to_clear")
        assert service.get_or_create_context("user_to_clear").user_id == "user_to_clear"

        service.clear_context("user_to_clear")
        # After clear, should get fresh context
        new_ctx = service.get_or_create_context("user_to_clear")
        assert new_ctx.monitoring_active is False


class TestAnalyzePortfolioDrift:
    """Tests for portfolio drift analysis."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        svc = AgentOrchestrationService()
        # Set up context with a profile
        profile = PersonalFinancialProfile(
            user_id=uuid4(),
            total_investments=50000,
            holdings=[
                HoldingAsset(
                    symbol="AAPL",
                    quantity=100,
                    current_value=17500,
                    cost_basis=15000,
                    unrealized_gain=2500,
                    unrealized_gain_percent=16.67,
                ),
                HoldingAsset(
                    symbol="GOOGL",
                    quantity=10,
                    current_value=29000,
                    cost_basis=25000,
                    unrealized_gain=4000,
                    unrealized_gain_percent=16.0,
                ),
            ],
            last_updated=datetime.now(),
        )
        ctx = svc.get_or_create_context("test_user")
        ctx.profile = profile
        return svc

    @pytest.mark.asyncio
    async def test_analyze_drift_returns_summary(self, service):
        """Should return a portfolio drift summary."""
        result = await service.analyze_portfolio_drift("test_user")
        assert result is not None
        assert hasattr(result, "total_value")
        assert hasattr(result, "drift_score")
        assert hasattr(result, "overweight_positions")
        assert hasattr(result, "underweight_positions")
        assert hasattr(result, "rebalancing_trades")

    @pytest.mark.asyncio
    async def test_analyze_drift_no_profile(self, service):
        """Should return None if no profile exists."""
        result = await service.analyze_portfolio_drift("nonexistent_user")
        assert result is None


class TestTaxLossHarvesting:
    """Tests for tax-loss harvesting tool."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        svc = AgentOrchestrationService()
        profile = PersonalFinancialProfile(
            user_id=uuid4(),
            total_investments=100000,
            holdings=[
                HoldingAsset(
                    symbol="AAPL",
                    quantity=100,
                    current_value=14000,  # Loss position
                    cost_basis=15000,
                    unrealized_gain=-1000,
                    unrealized_gain_percent=-6.67,
                ),
            ],
            last_updated=datetime.now(),
        )
        ctx = svc.get_or_create_context("test_user")
        ctx.profile = profile
        return svc

    @pytest.mark.asyncio
    async def test_check_tax_harvesting(self, service):
        """Should return harvesting opportunities."""
        result = await service.check_tax_loss_harvesting("test_user")
        assert result is not None
        assert hasattr(result, "total_unrealized_loss")
        assert hasattr(result, "candidates")
        assert hasattr(result, "harvesting_trades")

    @pytest.mark.asyncio
    async def test_check_tax_harvesting_no_profile(self, service):
        """Should return None without profile."""
        result = await service.check_tax_loss_harvesting("nonexistent_user")
        assert result is None


class TestGoalProgress:
    """Tests for goal progress checking."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        svc = AgentOrchestrationService()
        profile = PersonalFinancialProfile(
            user_id=uuid4(),
            monthly_income=10000,
            monthly_expenses=6000,
            last_updated=datetime.now(),
        )
        ctx = svc.get_or_create_context("test_user")
        ctx.profile = profile
        ctx.goals = [
            GoalDefinition(
                id=uuid4(),
                user_id=uuid4(),
                name="Emergency Fund",
                goal_type=GoalType.EMERGENCY_FUND,
                target_amount=50000,
                current_amount=30000,
                monthly_contribution=1000,
                target_date=date(2027, 1, 1),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        return svc

    @pytest.mark.asyncio
    async def test_check_goal_progress(self, service):
        """Should return progress for all goals."""
        progress_list = await service.check_goal_progress("test_user")
        assert len(progress_list) == 1
        assert progress_list[0].goal_name == "Emergency Fund"
        assert progress_list[0].progress_percent == 60.0

    @pytest.mark.asyncio
    async def test_check_goal_progress_empty_goals(self, service):
        """Should return empty list if no goals."""
        ctx = service.get_or_create_context("no_goals_user")
        ctx.goals = []
        progress_list = await service.check_goal_progress("no_goals_user")
        assert progress_list == []


class TestRebalancingRecommendation:
    """Tests for rebalancing recommendation generation."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        svc = AgentOrchestrationService()
        # Pre-populate with drift result
        from app.schemas.agent_schemas import PortfolioDriftSummary
        ctx = svc.get_or_create_context("test_user")
        ctx.drift_result = PortfolioDriftSummary(
            total_value=50000,
            drift_score=15.0,
            overweight_positions=[{"symbol": "AAPL", "current_weight": 0.4, "recommended_weight": 0.3}],
            underweight_positions=[{"symbol": "GOOGL", "current_weight": 0.1, "recommended_weight": 0.2}],
            rebalancing_trades=[
                {"symbol": "AAPL", "action": "SELL", "quantity": 10, "value": 1750},
                {"symbol": "GOOGL", "action": "BUY", "quantity": 5, "value": 14500},
            ],
            analyzed_at=datetime.now(),
        )
        return svc

    @pytest.mark.asyncio
    async def test_generate_rebalancing_recommendation(self, service):
        """Should generate rebalancing recommendation."""
        result = await service.generate_rebalancing_recommendation("test_user")
        assert result is not None
        assert result.category == "portfolio_rebalance"
        assert len(result.actions) == 2
        assert result.requires_approval is True

    @pytest.mark.asyncio
    async def test_generate_rebalancing_conservative(self, service):
        """Conservative rebalancing should have lower priority."""
        result = await service.generate_rebalancing_recommendation("test_user", aggressive=False)
        assert result is not None
        # Non-aggressive should have priority 3
        assert result.priority == 3


class TestOpenFinanceSync:
    """Tests for Open Finance data sync."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return AgentOrchestrationService()

    @pytest.mark.asyncio
    async def test_sync_open_finance_returns_profile(self, service):
        """Should return a financial profile after sync."""
        # This will return empty profile without real credentials
        result = await service.sync_open_finance_data("test_user", OpenFinanceProvider.ESUN_BANK)
        assert result is not None
        assert isinstance(result, PersonalFinancialProfile)
        assert result.user_id is not None


class TestRetirementGap:
    """Tests for retirement gap calculation."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        svc = AgentOrchestrationService()
        profile = PersonalFinancialProfile(
            user_id=uuid4(),
            monthly_income=10000,
            monthly_expenses=6000,
            total_investments=50000,
            last_updated=datetime.now(),
        )
        ctx = svc.get_or_create_context("test_user")
        ctx.profile = profile
        ctx.goals = [
            GoalDefinition(
                id=uuid4(),
                user_id=uuid4(),
                name="Retirement",
                goal_type=GoalType.RETIREMENT,
                target_amount=1_000_000,
                current_amount=50000,
                monthly_contribution=1000,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        return svc

    @pytest.mark.asyncio
    async def test_calculate_retirement_gap(self, service):
        """Should return retirement gap result."""
        goal = service.get_or_create_context("test_user").goals[0]
        result = await service.calculate_retirement_gap("test_user", goal, current_age=30, retirement_age=65)
        assert result is not None
        assert hasattr(result, "gap_amount")
        assert hasattr(result, "success_probability")
        assert hasattr(result, "monthly_shortfall")
        assert 0.0 <= result.success_probability <= 1.0


class TestRecommendationConversion:
    """Tests for recommendation generation from analysis results."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        svc = AgentOrchestrationService()
        svc.transition(AgentEvent.ANALYZE_NOW)
        return svc

    def test_drift_to_recommendations_low_drift(self, service):
        """Low drift score should produce no recommendations."""
        from app.schemas.agent_schemas import PortfolioDriftSummary
        drift = PortfolioDriftSummary(
            total_value=50000,
            drift_score=3.0,  # Below threshold
            overweight_positions=[],
            underweight_positions=[],
            rebalancing_trades=[],
            analyzed_at=datetime.now(),
        )
        recs = service._drift_to_recommendations(drift)
        assert recs == []

    def test_drift_to_recommendations_high_drift(self, service):
        """High drift score should produce recommendations."""
        from app.schemas.agent_schemas import PortfolioDriftSummary
        drift = PortfolioDriftSummary(
            total_value=50000,
            drift_score=25.0,  # Above threshold
            overweight_positions=[],
            underweight_positions=[],
            rebalancing_trades=[
                {"symbol": "AAPL", "action": "SELL", "quantity": 10, "value": 1750},
            ],
            analyzed_at=datetime.now(),
        )
        recs = service._drift_to_recommendations(drift)
        assert len(recs) == 1
        assert recs[0].category == "portfolio_drift"
        assert len(recs[0].actions) == 1


class TestMonitoringLoop:
    """Tests for the monitoring loop functionality."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance."""
        return AgentOrchestrationService()

    @pytest.mark.asyncio
    async def test_start_monitoring_sets_active(self, service):
        """Starting monitoring should set monitoring_active flag."""
        await service.start_monitoring("test_user")
        ctx = service.get_or_create_context("test_user")
        assert ctx.monitoring_active is True

    @pytest.mark.asyncio
    async def test_stop_monitoring_clears_active(self, service):
        """Stopping monitoring should clear monitoring_active flag."""
        await service.start_monitoring("test_user")
        await service.stop_monitoring("test_user")
        ctx = service.get_or_create_context("test_user")
        assert ctx.monitoring_active is False

    @pytest.mark.asyncio
    async def test_start_monitoring_transitions_state(self, service):
        """Starting monitoring should transition to MONITORING state."""
        await service.start_monitoring("test_user")
        assert service.state == AgentState.MONITORING

    @pytest.mark.asyncio
    async def test_stop_monitoring_transitions_to_idle(self, service):
        """Stopping monitoring should transition back to IDLE."""
        await service.start_monitoring("test_user")
        await service.stop_monitoring("test_user")
        assert service.state == AgentState.IDLE

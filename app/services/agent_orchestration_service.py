"""
AI Agent Orchestration Service

FSM-based orchestration for portfolio management AI agent with
LangChain-style tool calling and goal-based monitoring.
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from app.schemas.agent_schemas import (
    AgentAction,
    AgentRecommendation,
    AgentState,
    GoalDefinition,
    GoalProgress,
    GoalType,
    PersonalFinancialProfile,
    PortfolioDriftSummary,
    RetirementGapResult,
)
from app.services.drift_detection_service import DriftDetectionService
from app.services.goal_monitoring_service import GoalMonitoringService
from app.services.open_finance_adapter import (
    BaseOpenFinanceAdapter,
    OpenFinanceAdapterFactory,
    OpenFinanceProvider,
)
from app.services.tax_loss_harvesting_service import TaxLossHarvestingService, TaxLossHarvestingResult


# LangChain-style tool definition
@dataclass
class Tool:
    """Definition of a callable tool for the agent."""

    name: str
    description: str
    func: Callable
    parameters: dict = field(default_factory=dict)


class AgentEvent(str, Enum):
    """Events that can trigger state transitions."""

    START_MONITORING = "START_MONITORING"
    STOP_MONITORING = "STOP_MONITORING"
    ANALYZE_NOW = "ANALYZE_NOW"
    RECOMMEND = "RECOMMEND"
    TAKE_ACTION = "TAKE_ACTION"
    ACTION_COMPLETE = "ACTION_COMPLETE"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


@dataclass
class OrchestrationContext:
    """Context maintained across agent orchestration cycles."""

    user_id: str
    profile: Optional[PersonalFinancialProfile] = None
    goals: list[GoalDefinition] = field(default_factory=list)
    goal_progress: list[GoalProgress] = field(default_factory=list)
    retirement_gap: Optional[RetirementGapResult] = None
    drift_result: Optional[PortfolioDriftSummary] = None
    recommendations: list[AgentRecommendation] = field(default_factory=list)
    last_analysis: Optional[datetime] = None
    monitoring_active: bool = False
    metadata: dict = field(default_factory=dict)


class AgentOrchestrationService:
    """FSM-based AI Agent orchestration for portfolio management.

    States: IDLE -> MONITORING -> ANALYZING -> RECOMMENDING -> ACTING -> IDLE
    """

    # State transition table: current_state -> event -> next_state
    STATE_TRANSITIONS: dict[AgentState, dict[AgentEvent, AgentState]] = {
        AgentState.IDLE: {
            AgentEvent.START_MONITORING: AgentState.MONITORING,
            AgentEvent.ANALYZE_NOW: AgentState.ANALYZING,
        },
        AgentState.MONITORING: {
            AgentEvent.STOP_MONITORING: AgentState.IDLE,
            AgentEvent.ANALYZE_NOW: AgentState.ANALYZING,
            AgentEvent.ERROR: AgentState.IDLE,
        },
        AgentState.ANALYZING: {
            AgentEvent.RECOMMEND: AgentState.RECOMMENDING,
            AgentEvent.ACTION_COMPLETE: AgentState.IDLE,
            AgentEvent.ERROR: AgentState.IDLE,
            AgentEvent.TIMEOUT: AgentState.IDLE,
        },
        AgentState.RECOMMENDING: {
            AgentEvent.TAKE_ACTION: AgentState.ACTING,
            AgentEvent.ACTION_COMPLETE: AgentState.IDLE,
            AgentEvent.ERROR: AgentState.IDLE,
        },
        AgentState.ACTING: {
            AgentEvent.ACTION_COMPLETE: AgentState.IDLE,
            AgentEvent.ERROR: AgentState.IDLE,
        },
    }

    # Tool registry
    TOOLS: dict[str, Tool] = {}

    def __init__(self):
        """Initialize the Agent Orchestration Service."""
        self._state = AgentState.IDLE
        self._contexts: dict[str, OrchestrationContext] = {}
        self._drift_service = DriftDetectionService()
        self._goal_monitoring = GoalMonitoringService()
        self._tax_service = TaxLossHarvestingService()
        self._monitoring_tasks: dict[str, asyncio.Task] = {}
        self._open_finance_adapters = OpenFinanceAdapterFactory.create_all()

        # Register LangChain-style tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register available tools for the agent."""
        self.TOOLS = {
            "analyze_portfolio_drift": Tool(
                name="analyze_portfolio_drift",
                description="Analyze portfolio drift from target allocation and AI signals. "
                "Returns overweight/underweight positions and rebalancing trades.",
                func=self._tool_analyze_drift,
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "target_allocation": {"type": "object"},
                    },
                    "required": ["user_id"],
                },
            ),
            "check_tax_loss_harvesting": Tool(
                name="check_tax_loss_harvesting",
                description="Check for tax-loss harvesting opportunities. "
                "Identifies positions with unrealized losses that can be harvested "
                "to offset capital gains.",
                func=self._tool_check_tax_harvesting,
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "risk_tolerance": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                    },
                    "required": ["user_id"],
                },
            ),
            "calculate_retirement_gap": Tool(
                name="calculate_retirement_gap",
                description="Calculate retirement planning gap using Monte Carlo simulation. "
                "Returns success probability, shortfall amount, and recommended contributions.",
                func=self._tool_calculate_retirement_gap,
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "current_age": {"type": "integer"},
                        "retirement_age": {"type": "integer"},
                    },
                    "required": ["user_id", "current_age", "retirement_age"],
                },
            ),
            "generate_rebalancing_recommendation": Tool(
                name="generate_rebalancing_recommendation",
                description="Generate portfolio rebalancing recommendation based on "
                "current holdings, target allocation, and AI signals.",
                func=self._tool_generate_rebalancing,
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "aggressive": {"type": "boolean", "default": False},
                    },
                    "required": ["user_id"],
                },
            ),
            "check_goal_progress": Tool(
                name="check_goal_progress",
                description="Check progress toward a specific financial goal. "
                "Returns current status, projected completion date, and alerts.",
                func=self._tool_check_goal_progress,
                parameters={
                    "type": "object",
                    "properties": {
                        "goal_id": {"type": "string"},
                        "user_id": {"type": "string"},
                    },
                    "required": ["goal_id", "user_id"],
                },
            ),
            "sync_open_finance_data": Tool(
                name="sync_open_finance_data",
                description="Sync financial data from Open Finance providers "
                "(E.Sun Bank, Yodlee, Plaid) and update the user's profile.",
                func=self._tool_sync_open_finance,
                parameters={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "provider": {
                            "type": "string",
                            "enum": ["ESUN_BANK", "YODLEE", "PLAID"],
                        },
                    },
                    "required": ["user_id", "provider"],
                },
            ),
        }

    # -------------------------------------------------------------------------
    # FSM State Management
    # -------------------------------------------------------------------------

    @property
    def state(self) -> AgentState:
        """Get current FSM state."""
        return self._state

    def transition(self, event: AgentEvent) -> AgentState:
        """Transition to a new state based on event.

        Args:
            event: The event triggering the transition.

        Returns:
            The new state after transition.

        Raises:
            ValueError: If the transition is not allowed.
        """
        next_state = self.STATE_TRANSITIONS.get(self._state, {}).get(event)

        if next_state is None:
            raise ValueError(
                f"Invalid transition: {self._state.value} + {event.value} -> not allowed"
            )

        self._state = next_state
        return next_state

    def get_available_tools(self) -> list[Tool]:
        """Get list of available tools in current state.

        Returns:
            List of Tool definitions available for the current state.
        """
        # All tools are available in non-IDLE states
        if self._state == AgentState.IDLE:
            return []
        return list(self.TOOLS.values())

    # -------------------------------------------------------------------------
    # Context Management
    # -------------------------------------------------------------------------

    def get_or_create_context(self, user_id: str) -> OrchestrationContext:
        """Get or create orchestration context for a user.

        Args:
            user_id: The user's ID.

        Returns:
            The user's OrchestrationContext.
        """
        if user_id not in self._contexts:
            self._contexts[user_id] = OrchestrationContext(user_id=user_id)
        return self._contexts[user_id]

    def clear_context(self, user_id: str) -> None:
        """Clear orchestration context for a user.

        Args:
            user_id: The user's ID.
        """
        if user_id in self._contexts:
            del self._contexts[user_id]

    # -------------------------------------------------------------------------
    # Goal-Based Monitoring Loop
    # -------------------------------------------------------------------------

    async def start_monitoring(
        self,
        user_id: str,
        interval_seconds: int = 3600,
    ) -> None:
        """Start goal-based monitoring loop for a user.

        Args:
            user_id: The user's ID.
            interval_seconds: How often to run monitoring checks (default 1 hour).
        """
        ctx = self.get_or_create_context(user_id)
        ctx.monitoring_active = True

        # Transition to monitoring state
        try:
            self.transition(AgentEvent.START_MONITORING)
        except ValueError:
            # Already monitoring, just update
            pass

        # Cancel existing task if any
        if user_id in self._monitoring_tasks:
            self._monitoring_tasks[user_id].cancel()

        # Start new monitoring loop
        self._monitoring_tasks[user_id] = asyncio.create_task(
            self._monitoring_loop(user_id, interval_seconds)
        )

    async def stop_monitoring(self, user_id: str) -> None:
        """Stop monitoring loop for a user.

        Args:
            user_id: The user's ID.
        """
        ctx = self.get_or_create_context(user_id)
        ctx.monitoring_active = False

        if user_id in self._monitoring_tasks:
            self._monitoring_tasks[user_id].cancel()
            del self._monitoring_tasks[user_id]

        self.transition(AgentEvent.STOP_MONITORING)

    async def _monitoring_loop(self, user_id: str, interval_seconds: int) -> None:
        """Internal monitoring loop that runs periodic checks.

        Args:
            user_id: The user's ID.
            interval_seconds: Check interval.
        """
        while True:
            try:
                ctx = self.get_or_create_context(user_id)
                if not ctx.monitoring_active:
                    break

                # Run analysis cycle
                await self.run_analysis_cycle(user_id)

                # Wait for next interval
                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception:
                # Log and continue
                try:
                    self.transition(AgentEvent.ERROR)
                except ValueError:
                    pass
                await asyncio.sleep(interval_seconds)

    async def run_analysis_cycle(self, user_id: str) -> list[AgentRecommendation]:
        """Run a complete analysis cycle for a user.

        This is the main goal-based monitoring cycle that:
        1. Analyzes portfolio drift
        2. Checks tax-loss harvesting opportunities
        3. Calculates retirement gap
        4. Checks goal progress
        5. Generates recommendations

        Args:
            user_id: The user's ID.

        Returns:
            List of recommendations generated during the cycle.
        """
        ctx = self.get_or_create_context(user_id)

        # Transition to analyzing
        try:
            self.transition(AgentEvent.ANALYZE_NOW)
        except ValueError:
            pass

        recommendations: list[AgentRecommendation] = []

        try:
            # 1. Analyze portfolio drift
            drift_result = await self.analyze_portfolio_drift(user_id)
            if drift_result:
                ctx.drift_result = drift_result
                recommendations.extend(self._drift_to_recommendations(drift_result))

            # 2. Check tax-loss harvesting
            tax_result = await self.check_tax_loss_harvesting(user_id)
            if tax_result:
                recommendations.extend(self._tax_to_recommendations(tax_result))

            # 3. Calculate retirement gap if applicable
            for goal in ctx.goals:
                if goal.goal_type == GoalType.RETIREMENT:
                    retirement_gap = await self.calculate_retirement_gap(
                        user_id,
                        goal,
                        ctx.metadata.get("current_age", 30),
                        ctx.metadata.get("retirement_age", 65),
                    )
                    if retirement_gap:
                        ctx.retirement_gap = retirement_gap
                        recommendations.extend(self._retirement_to_recommendations(retirement_gap))

            # 4. Check all goal progress
            goal_progress_list = await self.check_goal_progress(user_id)
            ctx.goal_progress = goal_progress_list
            recommendations.extend(self._goals_to_recommendations(goal_progress_list))

            # Store recommendations
            ctx.recommendations = recommendations
            ctx.last_analysis = datetime.now()

            # Transition to recommending
            try:
                self.transition(AgentEvent.RECOMMEND)
            except ValueError:
                pass

        except Exception:
            try:
                self.transition(AgentEvent.ERROR)
            except ValueError:
                pass
            raise

        return recommendations

    # -------------------------------------------------------------------------
    # Core Analysis Methods
    # -------------------------------------------------------------------------

    async def analyze_portfolio_drift(self, user_id: str) -> Optional[PortfolioDriftSummary]:
        """Analyze portfolio drift from target allocation.

        Args:
            user_id: The user's ID.

        Returns:
            PortfolioDriftSummary with drift analysis.
        """
        ctx = self.get_or_create_context(user_id)

        if not ctx.profile:
            return None

        holdings = [
            {
                "symbol": h.symbol,
                "quantity": h.quantity,
                "avg_cost": h.cost_basis / h.quantity if h.quantity > 0 else 0,
            }
            for h in ctx.profile.holdings
        ]

        prices = {h.symbol: h.current_value / h.quantity if h.quantity > 0 else 0 for h in ctx.profile.holdings}

        # Mock signals for now (in production, would use signal engine)
        signals = {h.symbol: {"signal": "HOLD", "confidence": 0.5} for h in ctx.profile.holdings}

        total_value = ctx.profile.total_investments

        result = await self._drift_service.calculate_drift(
            holdings=holdings,
            prices=prices,
            signals=signals,
            portfolio_value=total_value,
        )

        return PortfolioDriftSummary(
            total_value=result.total_value,
            drift_score=result.drift_score,
            overweight_positions=[
                {
                    "symbol": h.symbol,
                    "current_weight": h.current_weight,
                    "recommended_weight": h.recommended_weight,
                    "drift": h.drift_percentage,
                }
                for h in result.holdings
                if h.action == "SELL"
            ],
            underweight_positions=[
                {
                    "symbol": h.symbol,
                    "current_weight": h.current_weight,
                    "recommended_weight": h.recommended_weight,
                    "drift": h.drift_percentage,
                }
                for h in result.holdings
                if h.action == "BUY"
            ],
            rebalancing_trades=[
                {
                    "symbol": h.symbol,
                    "action": h.action,
                    "quantity": h.action_quantity,
                    "value": h.action_value,
                }
                for h in result.rebalancing_trades
            ],
            estimated_tax_impact=None,  # Would calculate from tax service
            analyzed_at=datetime.now(),
        )

    async def check_tax_loss_harvesting(
        self,
        user_id: str,
        risk_tolerance: str = "MEDIUM",
    ) -> Optional[TaxLossHarvestingResult]:
        """Check for tax-loss harvesting opportunities.

        Args:
            user_id: The user's ID.
            risk_tolerance: LOW, MEDIUM, or HIGH.

        Returns:
            TaxLossHarvestingResult with harvesting opportunities.
        """
        ctx = self.get_or_create_context(user_id)

        if not ctx.profile:
            return None

        holdings = [
            {
                "symbol": h.symbol,
                "quantity": h.quantity,
                "avg_cost": h.cost_basis / h.quantity if h.quantity > 0 else h.cost_basis,
            }
            for h in ctx.profile.holdings
            if h.quantity > 0
        ]

        prices = {h.symbol: h.current_value / h.quantity if h.quantity > 0 else 0 for h in ctx.profile.holdings if h.quantity > 0}

        return self._tax_service.calculate_harvesting_opportunities(
            holdings=holdings,
            prices=prices,
            risk_tolerance=risk_tolerance,
        )

    async def calculate_retirement_gap(
        self,
        user_id: str,
        retirement_goal: GoalDefinition,
        current_age: int,
        retirement_age: int,
    ) -> Optional[RetirementGapResult]:
        """Calculate retirement planning gap.

        Args:
            user_id: The user's ID.
            retirement_goal: The retirement goal definition.
            current_age: User's current age.
            retirement_age: Target retirement age.

        Returns:
            RetirementGapResult with gap analysis.
        """
        ctx = self.get_or_create_context(user_id)

        return await self._goal_monitoring.calculate_retirement_gap(
            goal=retirement_goal,
            profile=ctx.profile or PersonalFinancialProfile(
                user_id=ctx.profile.user_id if ctx.profile else uuid.uuid4(),
                last_updated=datetime.now(),
            ),
            current_age=current_age,
            retirement_age=retirement_age,
        )

    async def generate_rebalancing_recommendation(
        self,
        user_id: str,
        aggressive: bool = False,
    ) -> Optional[AgentRecommendation]:
        """Generate portfolio rebalancing recommendation.

        Args:
            user_id: The user's ID.
            aggressive: If True, recommend larger trades for faster rebalancing.

        Returns:
            AgentRecommendation for rebalancing.
        """
        ctx = self.get_or_create_context(user_id)

        if not ctx.drift_result:
            # Run drift analysis first
            await self.analyze_portfolio_drift(user_id)

        if not ctx.drift_result or not ctx.drift_result.rebalancing_trades:
            return None

        drift = ctx.drift_result

        actions = [
            AgentAction(
                action_id=str(uuid.uuid4()),
                action_type="REBALANCE",
                priority=1 if aggressive else 3,
                description=f"{trade['action']} {trade['quantity']:.2f} shares of {trade['symbol']}",
                rationale=f"Current weight deviates from target. Estimated value: ${trade['value']:.2f}",
                metadata=trade,
                confidence=0.8,
                created_at=datetime.now(),
            )
            for trade in drift.rebalancing_trades
        ]

        return AgentRecommendation(
            recommendation_id=str(uuid.uuid4()),
            agent_state=self._state,
            category="portfolio_rebalance",
            title="Portfolio Rebalancing Recommended",
            description=f"Detected {len(actions)} trades to bring portfolio back to target allocation. "
            f"Drift score: {drift.drift_score:.1f}/100",
            actions=actions,
            priority=3,
            confidence=0.8,
            risk_level="MODERATE",
            requires_approval=True,
            created_at=datetime.now(),
        )

    async def check_goal_progress(self, user_id: str) -> list[GoalProgress]:
        """Check progress for all user goals.

        Args:
            user_id: The user's ID.

        Returns:
            List of GoalProgress for each goal.
        """
        ctx = self.get_or_create_context(user_id)

        progress_list: list[GoalProgress] = []

        for goal in ctx.goals:
            progress = await self._goal_monitoring.check_goal_progress(goal, ctx.profile)
            progress_list.append(progress)

        return progress_list

    # -------------------------------------------------------------------------
    # Open Finance Integration
    # -------------------------------------------------------------------------

    async def sync_open_finance_data(
        self,
        user_id: str,
        provider: OpenFinanceProvider,
    ) -> PersonalFinancialProfile:
        """Sync financial data from an Open Finance provider.

        Args:
            user_id: The user's ID.
            provider: The Open Finance provider to sync from.

        Returns:
            Updated PersonalFinancialProfile.
        """
        ctx = self.get_or_create_context(user_id)

        adapter = OpenFinanceAdapterFactory.create(provider)

        # Sync accounts and holdings
        # In production, would retrieve actual connection from database
        connections = ctx.profile.connections if ctx.profile else []

        if connections:
            profile = await adapter.build_profile(uuid.UUID(user_id), connections)
        else:
            # Create empty profile if no connections
            # Handle non-UUID user_ids gracefully
            try:
                profile_uuid = uuid.UUID(user_id)
            except (ValueError, AttributeError):
                profile_uuid = uuid.uuid4()
            profile = PersonalFinancialProfile(
                user_id=profile_uuid,
                last_updated=datetime.now(),
            )

        ctx.profile = profile
        return profile

    # -------------------------------------------------------------------------
    # LangChain-Style Tool Calling
    # -------------------------------------------------------------------------

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name.

        Args:
            name: Tool name.

        Returns:
            Tool definition or None.
        """
        return self.TOOLS.get(name)

    def list_tools(self) -> list[dict]:
        """List all available tools.

        Returns:
            List of tool definitions suitable for LangChain tool registry.
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in self.TOOLS.values()
        ]

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ) -> Any:
        """Call a tool with arguments (LangChain-style).

        Args:
            tool_name: Name of the tool to call.
            arguments: Tool arguments.

        Returns:
            Tool execution result.

        Raises:
            ValueError: If tool not found or invalid arguments.
        """
        tool = self.TOOLS.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        return await tool.func(**arguments)

    # -------------------------------------------------------------------------
    # Tool Implementations (private)
    # -------------------------------------------------------------------------

    async def _tool_analyze_drift(self, user_id: str, **kwargs) -> PortfolioDriftSummary:
        """Tool: analyze_portfolio_drift."""
        return await self.analyze_portfolio_drift(user_id)

    async def _tool_check_tax_harvesting(
        self,
        user_id: str,
        risk_tolerance: str = "MEDIUM",
        **kwargs,
    ) -> TaxLossHarvestingResult:
        """Tool: check_tax_loss_harvesting."""
        return await self.check_tax_loss_harvesting(user_id, risk_tolerance)

    async def _tool_calculate_retirement_gap(
        self,
        user_id: str,
        current_age: int,
        retirement_age: int,
        **kwargs,
    ) -> RetirementGapResult:
        """Tool: calculate_retirement_gap."""
        ctx = self.get_or_create_context(user_id)

        # Find retirement goal
        retirement_goal = next(
            (g for g in ctx.goals if g.goal_type == GoalType.RETIREMENT),
            GoalDefinition(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id),
                name="Retirement",
                goal_type=GoalType.RETIREMENT,
                target_amount=1_000_000,
                current_amount=ctx.profile.total_investments if ctx.profile else 0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        )

        return await self.calculate_retirement_gap(user_id, retirement_goal, current_age, retirement_age)

    async def _tool_generate_rebalancing(
        self,
        user_id: str,
        aggressive: bool = False,
        **kwargs,
    ) -> AgentRecommendation:
        """Tool: generate_rebalancing_recommendation."""
        return await self.generate_rebalancing_recommendation(user_id, aggressive)

    async def _tool_check_goal_progress(
        self,
        goal_id: str,
        user_id: str,
        **kwargs,
    ) -> GoalProgress:
        """Tool: check_goal_progress."""
        ctx = self.get_or_create_context(user_id)

        goal = next(
            (g for g in ctx.goals if str(g.id) == goal_id),
            None,
        )

        if not goal:
            raise ValueError(f"Goal not found: {goal_id}")

        return await self._goal_monitoring.check_goal_progress(goal, ctx.profile)

    async def _tool_sync_open_finance(
        self,
        user_id: str,
        provider: str,
        **kwargs,
    ) -> PersonalFinancialProfile:
        """Tool: sync_open_finance_data."""
        return await self.sync_open_finance_data(user_id, OpenFinanceProvider(provider))

    # -------------------------------------------------------------------------
    # Recommendation Helpers
    # -------------------------------------------------------------------------

    def _drift_to_recommendations(
        self,
        drift: PortfolioDriftSummary,
    ) -> list[AgentRecommendation]:
        """Convert drift analysis to recommendations."""
        if drift.drift_score < 5:
            return []

        actions = [
            AgentAction(
                action_id=str(uuid.uuid4()),
                action_type="REBALANCE",
                priority=3 if drift.drift_score < 20 else 2,
                description=f"{trade['action']} {trade['quantity']:.2f} {trade['symbol']}",
                rationale=f"Drift: {abs(drift.drift_score - 50):.1f}% from target",
                metadata=trade,
                confidence=0.75,
                created_at=datetime.now(),
            )
            for trade in drift.rebalancing_trades
        ]

        return [
            AgentRecommendation(
                recommendation_id=str(uuid.uuid4()),
                agent_state=self._state,
                category="portfolio_drift",
                title=f"Portfolio Drift: {drift.drift_score:.1f}/100",
                description=f"Portfolio has drifted {drift.drift_score:.1f}% from target allocation. "
                f"{len(drift.rebalancing_trades)} trades recommended.",
                actions=actions,
                priority=3 if drift.drift_score < 20 else 2,
                confidence=0.75,
                risk_level="LOW",
                requires_approval=True,
                created_at=datetime.now(),
            )
        ]

    def _tax_to_recommendations(
        self,
        tax_result: TaxLossHarvestingResult,
    ) -> list[AgentRecommendation]:
        """Convert tax-loss harvesting result to recommendations."""
        if not tax_result.harvesting_trades:
            return []

        actions = [
            AgentAction(
                action_id=str(uuid.uuid4()),
                action_type="TAX_HARVEST",
                priority=2,
                description=f"HARVEST {candidate.symbol} - Loss: ${candidate.unrealized_loss:.2f}",
                rationale=f"Estimated tax savings: ${candidate.estimated_tax_savings:.2f}",
                metadata={
                    "symbol": candidate.symbol,
                    "loss": candidate.unrealized_loss,
                    "tax_savings": candidate.estimated_tax_savings,
                    "wash_sale_risk": candidate.wash_sale_risk,
                },
                confidence=0.85,
                created_at=datetime.now(),
            )
            for candidate in tax_result.harvesting_trades
        ]

        return [
            AgentRecommendation(
                recommendation_id=str(uuid.uuid4()),
                agent_state=self._state,
                category="tax_loss_harvesting",
                title="Tax-Loss Harvesting Opportunities",
                description=f"Found {len(tax_result.harvesting_trades)} positions with losses to harvest. "
                f"Total estimated tax savings: ${tax_result.total_estimated_tax_savings:.2f}",
                actions=actions,
                priority=2,
                confidence=0.85,
                risk_level="MODERATE",
                requires_approval=True,
                created_at=datetime.now(),
            )
        ]

    def _retirement_to_recommendations(
        self,
        gap: RetirementGapResult,
    ) -> list[AgentRecommendation]:
        """Convert retirement gap to recommendations."""
        if gap.success_probability >= 0.80 and gap.gap_percentage < 10:
            return []

        actions = [
            AgentAction(
                action_id=str(uuid.uuid4()),
                action_type="GOAL_ADJUST",
                priority=1 if gap.success_probability < 0.70 else 2,
                description=f"Increase monthly contribution by ${gap.monthly_shortfall:.2f}",
                rationale=f"Current success probability: {gap.success_probability:.0%}. "
                f"Gap: ${gap.gap_amount:.2f}",
                metadata={
                    "gap_amount": gap.gap_amount,
                    "gap_percentage": gap.gap_percentage,
                    "success_probability": gap.success_probability,
                },
                confidence=0.80,
                created_at=datetime.now(),
            )
        ]

        return [
            AgentRecommendation(
                recommendation_id=str(uuid.uuid4()),
                agent_state=self._state,
                category="retirement_planning",
                title="Retirement Plan Adjustment Needed",
                description=f"Retirement success probability: {gap.success_probability:.0%}. "
                f"Gap: ${gap.gap_amount:.2f} ({gap.gap_percentage:.1f}% short). "
                f"Recommended monthly contribution: ${gap.recommended_monthly_contribution:.2f}",
                actions=actions,
                priority=1 if gap.success_probability < 0.70 else 2,
                confidence=0.80,
                risk_level="HIGH" if gap.success_probability < 0.70 else "MODERATE",
                requires_approval=False,  # Can auto-implement contribution changes
                created_at=datetime.now(),
            )
        ]

    def _goals_to_recommendations(
        self,
        progress_list: list[GoalProgress],
    ) -> list[AgentRecommendation]:
        """Convert goal progress to recommendations."""
        recommendations: list[AgentRecommendation] = []

        for progress in progress_list:
            if not progress.on_track and progress.status.value in ("AT_RISK", "BEHIND"):
                actions = [
                    AgentAction(
                        action_id=str(uuid.uuid4()),
                        action_type="GOAL_ADJUST",
                        priority=2 if progress.status.value == "AT_RISK" else 1,
                        description=f"Increase monthly contribution to ${progress.monthly_needed:.2f}",
                        rationale=f"Goal '{progress.goal_name}' is {progress.status.value}. "
                        f"Gap: ${progress.gap_amount:.2f}",
                        metadata={
                            "goal_id": str(progress.goal_id),
                            "gap_amount": progress.gap_amount,
                            "monthly_needed": progress.monthly_needed,
                        },
                        confidence=0.75,
                        created_at=datetime.now(),
                    )
                ]

                recommendations.append(
                    AgentRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        agent_state=self._state,
                        category="goal_adjustment",
                        title=f"Goal '{progress.goal_name}' Needs Attention",
                        description=f"Progress: {progress.progress_percent:.1f}%. "
                        f"Status: {progress.status.value}. "
                        f"Projected completion: {progress.projected_completion}",
                        actions=actions,
                        priority=2 if progress.status.value == "AT_RISK" else 1,
                        confidence=0.75,
                        risk_level="MODERATE",
                        requires_approval=True,
                        created_at=datetime.now(),
                    )
                )

        return recommendations

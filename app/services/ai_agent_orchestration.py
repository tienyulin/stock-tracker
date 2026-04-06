"""
AI Agent Orchestration Core Service.
Autonomous portfolio agent with goal-based monitoring, drift detection, and tax-loss harvesting.
"""
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from app.core.database import get_db
from app.api.v1.auth import get_current_user


class AgentState(str, Enum):
    IDLE = "idle"
    MONITORING = "monitoring"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    ALERTING = "alerting"
    DONE = "done"


class AgentEvent(str, Enum):
    START_MONITORING = "start_monitoring"
    GOAL_SET = "goal_set"
    DRIFT_DETECTED = "drift_detected"
    THRESHOLD_BREACHED = "threshold_breached"
    TAX_LOSS_OPPORTUNITY = "tax_loss_opportunity"
    USER_APPROVED = "user_approved"
    USER_REJECTED = "user_rejected"
    EXECUTE_REBALANCE = "execute_rebalance"
    EXECUTE_TLH = "execute_tlh"
    CHECK_COMPLETE = "check_complete"
    STOP = "stop"


@dataclass
class Goal:
    id: str
    name: str
    target_value: float
    current_value: float
    threshold_percent: float = 0.10
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Alert:
    id: str
    type: str  # "drift", "tax_loss", "rebalance"
    severity: str  # "low", "medium", "high"
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False


class AIAgentOrchestration:
    """
    FSM-based AI Agent for autonomous portfolio management.
    
    State Machine:
    IDLE -> MONITORING -> ANALYZING -> (WAITING_APPROVAL | ALERTING) -> DONE
                             -> EXECUTING -> DONE
    """
    
    def __init__(self, db, user_id: str):
        self.db = db
        self.user_id = user_id
        self.state = AgentState.IDLE
        self.goals: List[Goal] = []
        self.alerts: List[Alert] = []
        self.pending_actions: List[Dict[str, Any]] = []
        self._state_handlers: Dict[AgentState, Callable] = {}
        self._setup_state_handlers()
    
    def _setup_state_handlers(self):
        self._state_handlers = {
            AgentState.IDLE: self._handle_idle,
            AgentState.MONITORING: self._handle_monitoring,
            AgentState.ANALYZING: self._handle_analyzing,
            AgentState.EXECUTING: self._handle_executing,
            AgentState.WAITING_APPROVAL: self._handle_waiting_approval,
            AgentState.ALERTING: self._handle_alerting,
            AgentState.DONE: self._handle_done,
        }
    
    async def _transition(self, new_state: AgentState):
        self.state = new_state
        handler = self._state_handlers.get(new_state)
        if handler:
            await handler()
    
    async def _handle_idle(self):
        pass
    
    async def _handle_monitoring(self):
        # Monitor goals and check thresholds
        await self._check_goal_thresholds()
        await self._check_drift()
        await self._check_tax_loss_opportunities()
    
    async def _handle_analyzing(self):
        # Analyze detected issues
        pass
    
    async def _handle_executing(self):
        # Execute approved actions
        pass
    
    async def _handle_waiting_approval(self):
        # Wait for user approval
        pass
    
    async def _handle_alerting(self):
        # Send alerts to user
        pass
    
    async def _handle_done(self):
        pass
    
    async def _check_goal_thresholds(self):
        """Check if any goal thresholds are breached."""
        for goal in self.goals:
            deviation = abs(goal.current_value - goal.target_value) / goal.target_value
            if deviation > goal.threshold_percent:
                alert = Alert(
                    id=f"drift-{goal.id}-{datetime.utcnow().timestamp()}",
                    type="drift",
                    severity="high" if deviation > 0.2 else "medium",
                    message=f"Portfolio drift detected for goal '{goal.name}': {deviation*100:.1f}% deviation",
                    data={"goal_id": goal.id, "deviation": deviation}
                )
                self.alerts.append(alert)
                await self._transition(AgentState.ALERTING)
    
    async def _check_drift(self):
        """Check portfolio drift across all positions."""
        # Placeholder for drift detection integration
        pass
    
    async def _check_tax_loss_opportunities(self):
        """Check for tax-loss harvesting opportunities."""
        # Placeholder for tax-loss harvesting integration
        pass
    
    async def process_event(self, event: AgentEvent, data: Optional[Dict[str, Any]] = None):
        """Process an event and transition state accordingly."""
        if event == AgentEvent.START_MONITORING:
            await self._transition(AgentState.MONITORING)
        elif event == AgentEvent.GOAL_SET:
            await self._transition(AgentState.MONITORING)
        elif event == AgentEvent.DRIFT_DETECTED:
            await self._transition(AgentState.ANALYZING)
            await self._transition(AgentState.WAITING_APPROVAL)
        elif event == AgentEvent.THRESHOLD_BREACHED:
            await self._transition(AgentState.ALERTING)
        elif event == AgentEvent.USER_APPROVED:
            await self._transition(AgentState.EXECUTING)
        elif event == AgentEvent.USER_REJECTED:
            await self._transition(AgentState.DONE)
        elif event == AgentEvent.STOP:
            await self._transition(AgentState.DONE)
    
    def add_goal(self, name: str, target_value: float, current_value: float, threshold_percent: float = 0.10):
        """Add a monitoring goal."""
        goal = Goal(
            id=f"goal-{len(self.goals)+1}",
            name=name,
            target_value=target_value,
            current_value=current_value,
            threshold_percent=threshold_percent
        )
        self.goals.append(goal)
        return goal
    
    def get_alerts(self, unacknowledged_only: bool = False) -> List[Alert]:
        """Get all alerts."""
        if unacknowledged_only:
            return [a for a in self.alerts if not a.acknowledged]
        return self.alerts
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
    
    def get_state(self) -> Dict[str, Any]:
        """Get current agent state."""
        return {
            "state": self.state.value,
            "goals": [
                {
                    "id": g.id,
                    "name": g.name,
                    "target_value": g.target_value,
                    "current_value": g.current_value,
                    "threshold_percent": g.threshold_percent
                }
                for g in self.goals
            ],
            "alerts_count": len(self.alerts),
            "pending_actions_count": len(self.pending_actions)
        }

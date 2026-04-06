"""
AI Agent Orchestration API v1 routes.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/agent", tags=["AI Agent"])


class GoalRequest(BaseModel):
    name: str
    target_value: float
    current_value: float
    threshold_percent: float = 0.10


class GoalResponse(BaseModel):
    id: str
    name: str
    target_value: float
    current_value: float
    threshold_percent: float


class AlertResponse(BaseModel):
    id: str
    type: str
    severity: str
    message: str
    acknowledged: bool


class AgentStateResponse(BaseModel):
    state: str
    goals: List[GoalResponse]
    alerts_count: int
    pending_actions_count: int


class EventRequest(BaseModel):
    event: str  # start_monitoring, goal_set, stop
    data: Optional[dict] = None


@router.get("/state", response_model=AgentStateResponse)
async def get_agent_state(
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Get current AI agent state for the user.
    """
    from app.services.ai_agent_orchestration import AIAgentOrchestration
    
    agent = AIAgentOrchestration(db, current_user.id)
    state = agent.get_state()
    return state


@router.post("/goals", response_model=GoalResponse)
async def add_goal(
    request: GoalRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Add a new goal for the AI agent to monitor.
    """
    from app.services.ai_agent_orchestration import AIAgentOrchestration
    
    agent = AIAgentOrchestration(db, current_user.id)
    goal = agent.add_goal(
        name=request.name,
        target_value=request.target_value,
        current_value=request.current_value,
        threshold_percent=request.threshold_percent
    )
    return GoalResponse(
        id=goal.id,
        name=goal.name,
        target_value=goal.target_value,
        current_value=goal.current_value,
        threshold_percent=goal.threshold_percent
    )


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    unacknowledged_only: bool = False,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Get AI agent alerts.
    """
    from app.services.ai_agent_orchestration import AIAgentOrchestration
    
    agent = AIAgentOrchestration(db, current_user.id)
    alerts = agent.get_alerts(unacknowledged_only=unacknowledged_only)
    return [
        AlertResponse(
            id=a.id,
            type=a.type,
            severity=a.severity,
            message=a.message,
            acknowledged=a.acknowledged
        )
        for a in alerts
    ]


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Acknowledge an alert.
    """
    from app.services.ai_agent_orchestration import AIAgentOrchestration
    
    agent = AIAgentOrchestration(db, current_user.id)
    agent.acknowledge_alert(alert_id)
    return {"status": "ok"}


@router.post("/events")
async def post_event(
    request: EventRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Send an event to the AI agent state machine.
    """
    from app.services.ai_agent_orchestration import AIAgentOrchestration, AgentEvent
    
    agent = AIAgentOrchestration(db, current_user.id)
    
    event_map = {
        "start_monitoring": AgentEvent.START_MONITORING,
        "goal_set": AgentEvent.GOAL_SET,
        "stop": AgentEvent.STOP,
    }
    
    event = event_map.get(request.event)
    if not event:
        raise HTTPException(status_code=400, detail=f"Unknown event: {request.event}")
    
    await agent.process_event(event, request.data)
    return {"status": "ok", "state": agent.state.value}

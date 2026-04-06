"""
Automated Trading API — rule management and execution endpoints.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.models.trading_rule import OrderType, RuleStatus, RuleType, TradingRule
from app.schemas.schemas import PassiveIncomeSourceResponse  # reuse not available, inline
from app.services.automated_trading_service import AutomatedTradingService

router = APIRouter(prefix="/automated-trading", tags=["automated-trading"])
logger = logging.getLogger(__name__)


# ─── Schemas ───────────────────────────────────────────────────────────────────

class TradingRuleCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    rule_type: str = Field(..., description="price_trigger|indicator_signal|rebalance|schedule|ai_signal|dividend_reinvest")
    symbol: Optional[str] = Field(None, max_length=20)
    target_quantity: Optional[float] = None
    target_percentage: Optional[float] = None
    order_type: str = Field(default=OrderType.MARKET.value)
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    max_order_value: Optional[float] = None
    max_daily_loss: Optional[float] = None
    broker_connection_id: Optional[str] = None
    schedule_cron: Optional[str] = None
    expires_at: Optional[datetime] = None


class TradingRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    target_quantity: Optional[float] = None
    target_percentage: Optional[float] = None
    order_type: Optional[str] = None
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    max_order_value: Optional[float] = None
    max_daily_loss: Optional[float] = None
    broker_connection_id: Optional[str] = None
    expires_at: Optional[datetime] = None


class TradingRuleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    rule_type: str
    status: str
    symbol: Optional[str]
    target_quantity: Optional[float]
    target_percentage: Optional[float]
    order_type: str
    limit_price: Optional[float]
    stop_price: Optional[float]
    max_order_value: Optional[float]
    max_daily_loss: Optional[float]
    broker_connection_id: Optional[str]
    schedule_cron: Optional[str]
    trigger_count: int
    last_triggered_at: Optional[datetime]
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AutomationLogResponse(BaseModel):
    id: str
    rule_id: Optional[str]
    triggered_at: datetime
    trigger_reason: Optional[str]
    action_taken: str
    symbol: Optional[str]
    order_type: Optional[str]
    quantity: Optional[float]
    price: Optional[float]
    order_value: Optional[float]
    status: str
    broker_order_id: Optional[str]
    error_message: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class ExecutionStatsResponse(BaseModel):
    total_executions: int
    success: int
    failed: int
    skipped: int
    success_rate: float
    total_trade_value: float


class AiSignalTriggerRequest(BaseModel):
    symbol: str
    action: str = Field(..., description="buy or sell")
    confidence: float = Field(..., ge=0, le=1)
    reason: str
    quantity: Optional[float] = None


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.post("/rules", response_model=TradingRuleResponse, status_code=201)
async def create_rule(
    payload: TradingRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradingRuleResponse:
    """Create a new automated trading rule."""
    service = AutomatedTradingService(db)
    rule = service.create_rule(
        user_id=current_user.id,
        name=payload.name,
        rule_type=payload.rule_type,
        description=payload.description,
        symbol=payload.symbol,
        target_quantity=payload.target_quantity,
        target_percentage=payload.target_percentage,
        order_type=payload.order_type,
        limit_price=payload.limit_price,
        stop_price=payload.stop_price,
        max_order_value=payload.max_order_value,
        max_daily_loss=payload.max_daily_loss,
        broker_connection_id=payload.broker_connection_id,
        schedule_cron=payload.schedule_cron,
        expires_at=payload.expires_at,
    )
    return TradingRuleResponse.model_validate(rule)


@router.get("/rules", response_model=list[TradingRuleResponse])
async def list_rules(
    active_only: bool = Query(True),
    rule_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TradingRuleResponse]:
    """List all trading rules for the current user."""
    service = AutomatedTradingService(db)
    rules = service.get_rules(
        current_user.id, active_only=active_only, rule_type=rule_type
    )
    return [TradingRuleResponse.model_validate(r) for r in rules]


@router.get("/rules/{rule_id}", response_model=TradingRuleResponse)
async def get_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradingRuleResponse:
    """Get a specific trading rule."""
    from uuid import UUID
    try:
        rid = UUID(rule_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    service = AutomatedTradingService(db)
    rule = service.get_rule(current_user.id, rid)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return TradingRuleResponse.model_validate(rule)


@router.patch("/rules/{rule_id}", response_model=TradingRuleResponse)
async def update_rule(
    rule_id: str,
    payload: TradingRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradingRuleResponse:
    """Update a trading rule."""
    from uuid import UUID
    try:
        rid = UUID(rule_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    service = AutomatedTradingService(db)
    updates = payload.model_dump(exclude_unset=True)
    rule = service.update_rule(rid, current_user.id, **updates)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return TradingRuleResponse.model_validate(rule)


@router.post("/rules/{rule_id}/pause", response_model=TradingRuleResponse)
async def pause_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradingRuleResponse:
    """Pause a trading rule."""
    from uuid import UUID
    try:
        rid = UUID(rule_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    service = AutomatedTradingService(db)
    rule = service.pause_rule(current_user.id, rid)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return TradingRuleResponse.model_validate(rule)


@router.post("/rules/{rule_id}/resume", response_model=TradingRuleResponse)
async def resume_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradingRuleResponse:
    """Resume a paused trading rule."""
    from uuid import UUID
    try:
        rid = UUID(rule_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    service = AutomatedTradingService(db)
    rule = service.resume_rule(current_user.id, rid)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return TradingRuleResponse.model_validate(rule)


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a trading rule."""
    from uuid import UUID
    try:
        rid = UUID(rule_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID format")
    service = AutomatedTradingService(db)
    if not service.delete_rule(current_user.id, rid):
        raise HTTPException(status_code=404, detail="Rule not found")


# ─── Execution Logs ────────────────────────────────────────────────────────────

@router.get("/executions", response_model=list[AutomationLogResponse])
async def list_executions(
    rule_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AutomationLogResponse]:
    """List automation execution history."""
    from uuid import UUID
    rid = None
    if rule_id:
        try:
            rid = UUID(rule_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid rule ID format")
    service = AutomatedTradingService(db)
    logs = service.get_execution_logs(
        current_user.id, rule_id=rid, start_date=start_date, end_date=end_date, limit=limit
    )
    return [AutomationLogResponse.model_validate(log) for log in logs]


@router.get("/stats", response_model=ExecutionStatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExecutionStatsResponse:
    """Get automated trading statistics."""
    service = AutomatedTradingService(db)
    return ExecutionStatsResponse(**service.get_execution_stats(current_user.id))


# ─── AI Signal Trigger ─────────────────────────────────────────────────────────

@router.post("/trigger/ai-signal", response_model=Optional[AutomationLogResponse])
async def trigger_from_ai_signal(
    payload: AiSignalTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Optional[AutomationLogResponse]:
    """
    Trigger automated trade from AI signal.
    Only executes if user has an active AI_SIGNAL rule matching the symbol.
    """
    service = AutomatedTradingService(db)
    log = service.trigger_from_ai_signal(
        user_id=current_user.id,
        symbol=payload.symbol,
        action=payload.action,
        confidence=payload.confidence,
        reason=payload.reason,
        quantity=payload.quantity,
    )
    if not log:
        raise HTTPException(
            status_code=404,
            detail="No active AI signal rule found for this symbol. Please create one first.",
        )
    return AutomationLogResponse.model_validate(log)

"""
Alert API routes.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.utils.auth import decode_access_token
from app.models import Alert, AlertNotification, User
from app.schemas import AlertCreate, AlertResponse, AlertUpdate

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> List[AlertResponse]:
    """List all alerts for a user."""
    result = await db.execute(
        select(Alert).where(Alert.user_id == user_id).order_by(Alert.created_at)
    )
    alerts = result.scalars().all()

    return [
        AlertResponse(
            id=alert.id,
            symbol=alert.symbol,
            condition_type=alert.condition_type,
            threshold=alert.threshold,
            is_active=alert.is_active,
            triggered_at=alert.triggered_at,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
        )
        for alert in alerts
    ]


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """Create a new price alert."""
    alert = Alert(
        user_id=user_id,
        symbol=alert_data.symbol.upper(),
        condition_type=alert_data.condition_type,
        threshold=alert_data.threshold,
        is_active=True,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return AlertResponse(
        id=alert.id,
        symbol=alert.symbol,
        condition_type=alert.condition_type,
        threshold=alert.threshold,
        is_active=alert.is_active,
        triggered_at=alert.triggered_at,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """Get a specific alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return AlertResponse(
        id=alert.id,
        symbol=alert.symbol,
        condition_type=alert.condition_type,
        threshold=alert.threshold,
        is_active=alert.is_active,
        triggered_at=alert.triggered_at,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    alert_data: AlertUpdate,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """Update an alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert_data.is_active is not None:
        alert.is_active = alert_data.is_active
    if alert_data.condition_type is not None:
        alert.condition_type = alert_data.condition_type
    if alert_data.threshold is not None:
        alert.threshold = alert_data.threshold
    if alert_data.triggered_at is not None:
        alert.triggered_at = alert_data.triggered_at  # None = reset

    await db.commit()
    await db.refresh(alert)

    return AlertResponse(
        id=alert.id,
        symbol=alert.symbol,
        condition_type=alert.condition_type,
        threshold=alert.threshold,
        is_active=alert.is_active,
        triggered_at=alert.triggered_at,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete an alert."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    await db.delete(alert)
    await db.commit()


class AlertNotificationResponse(BaseModel):
    """Alert notification history response."""

    id: UUID
    alert_id: UUID
    channel: str
    status: str
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    symbol: str
    condition_type: str
    threshold: float
    triggered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get("/history", response_model=List[AlertNotificationResponse])
async def get_alert_history(
    user_id: UUID,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> List[AlertNotificationResponse]:
    """
    Get alert notification history for a user.

    Returns the history of triggered alert notifications,
    including the alert details and notification status.
    """
    # Get user's alerts first
    alerts_result = await db.execute(
        select(Alert.id).where(Alert.user_id == user_id)
    )
    alert_ids = [row[0] for row in alerts_result.fetchall()]

    if not alert_ids:
        return []

    # Get notifications for user's alerts, ordered by most recent
    result = await db.execute(
        select(AlertNotification, Alert)
        .join(Alert, AlertNotification.alert_id == Alert.id)
        .where(Alert.id.in_(alert_ids))
        .order_by(AlertNotification.sent_at.desc())
        .offset(offset)
        .limit(limit)
    )

    notifications = []
    for notification, alert in result.fetchall():
        notifications.append(
            AlertNotificationResponse(
                id=notification.id,
                alert_id=notification.alert_id,
                channel=notification.channel,
                status=notification.status,
                sent_at=notification.sent_at,
                error_message=notification.error_message,
                symbol=alert.symbol,
                condition_type=alert.condition_type,
                threshold=alert.threshold,
                triggered_at=alert.triggered_at,
            )
        )

    return notifications


class AlertCheckerResponse(BaseModel):
    """Response from alert checker run."""

    checked: int
    triggered: int
    errors: int
    checked_at: str


@router.post("/check", response_model=AlertCheckerResponse)
async def check_alerts(
    db: AsyncSession = Depends(get_db),
) -> AlertCheckerResponse:
    """
    Manually trigger alert checker.

    This endpoint checks all active alerts against current market prices
    and sends notifications for any triggered alerts.

    In production, this would be called by a scheduler every N minutes.
    """
    from app.services.alert_checker_service import AlertCheckerService

    checker = AlertCheckerService()
    result = await checker.check_all_alerts(db)

    return AlertCheckerResponse(**result)


@router.get("/dashboard", response_model=dict)
async def get_alert_dashboard(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get alert dashboard summary for a user.

    Returns:
        Dashboard with counts of active, triggered, and total alerts.
    """
    from sqlalchemy import func

    # Total alerts
    total_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.user_id == user_id)
    )
    total_alerts = total_result.scalar() or 0

    # Active alerts
    active_result = await db.execute(
        select(func.count(Alert.id)).where(
            and_(Alert.user_id == user_id, Alert.is_active == True)
        )
    )
    active_alerts = active_result.scalar() or 0

    # Triggered alerts (has triggered_at)
    triggered_result = await db.execute(
        select(func.count(Alert.id)).where(
            and_(Alert.user_id == user_id, Alert.triggered_at != None)
        )
    )
    triggered_alerts = triggered_result.scalar() or 0

    # Get unique symbols with active alerts
    symbols_result = await db.execute(
        select(Alert.symbol)
        .where(and_(Alert.user_id == user_id, Alert.is_active == True))
        .distinct()
    )
    monitored_symbols = [row[0] for row in symbols_result.fetchall()]

    return {
        "total_alerts": total_alerts,
        "active_alerts": active_alerts,
        "triggered_alerts": triggered_alerts,
        "monitored_symbols": monitored_symbols,
    }


@router.post("/{alert_id}/trigger", response_model=AlertResponse)
async def trigger_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    """Manually trigger an alert (for testing)."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    from datetime import datetime

    alert.triggered_at = datetime.utcnow()
    alert.is_active = False

    await db.commit()
    await db.refresh(alert)

    # Send LINE notification (async, non-blocking)
    from app.services.line_notify_service import notify_alert_triggered
    try:
        # Get current price for notification
        from app.services.yfinance_service import get_quote
        quote = await get_quote(alert.symbol)
        current_price = quote.get("regularMarketPrice") or quote.get("price") or alert.threshold
    except Exception:
        current_price = alert.threshold
    
    # Fire and forget - don't block the response
    try:
        await notify_alert_triggered(
            db=db,
            user_id=str(alert.user_id),
            symbol=alert.symbol,
            condition_type=alert.condition_type,
            threshold=alert.threshold,
            current_price=float(current_price)
        )
    except Exception as e:
        # Log but don't fail the request
        import logging
        logging.getLogger(__name__).warning(f"Failed to send LINE notification: {e}")

    # Send Discord notification (async, non-blocking)
    from app.services.discord_notify_service import notify_discord_alert_triggered
    try:
        # Get user's Discord webhook URL
        user_result = await db.execute(
            select(User.discord_webhook_url).where(User.id == alert.user_id)
        )
        discord_webhook_url = user_result.scalar_one_or_none()
        
        if discord_webhook_url:
            await notify_discord_alert_triggered(
                webhook_url=discord_webhook_url,
                symbol=alert.symbol,
                condition_type=alert.condition_type,
                threshold=alert.threshold,
                current_price=float(current_price)
            )
    except Exception as e:
        # Log but don't fail the request
        import logging
        logging.getLogger(__name__).warning(f"Failed to send Discord notification: {e}")

    return AlertResponse(
        id=alert.id,
        symbol=alert.symbol,
        condition_type=alert.condition_type,
        threshold=alert.threshold,
        is_active=alert.is_active,
        triggered_at=alert.triggered_at,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


# === Alerts Expansion Endpoints ===


class AlertConditionRequest(BaseModel):
    """Single alert condition."""
    metric: str
    operator: str
    value: float


class CreateExpandedAlertRequest(BaseModel):
    """Request to create an expanded alert."""
    symbol: str
    name: str
    conditions: List[AlertConditionRequest]
    notification_channels: List[str] = ["LINE"]
    custom_message: Optional[str] = None


class AlertResponse(BaseModel):
    """Alert response."""
    id: str
    symbol: str
    name: str
    conditions: List[dict]
    notification_channels: List[str]
    custom_message: str
    is_active: bool
    created_at: str


@router.post("/expanded", response_model=dict)
async def create_expanded_alert(
    request: CreateExpandedAlertRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
):
    """
    Create an expanded alert with multiple conditions.

    Supports:
    - Multiple alert types (price, percent, RSI, MACD)
    - AND/OR condition logic
    - Custom notification messages
    - Multiple notification channels
    """
    from app.services.alerts_expansion_service import AlertsExpansionService

    # Extract user ID from token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload["sub"]

    # Create alert (placeholder)
    _alert_service = AlertsExpansionService()

    conditions = [
        {"metric": c.metric, "operator": c.operator, "value": c.value}
        for c in request.conditions
    ]

    alert_data = {
        "id": f"alert_{user_id[:8]}_{request.symbol}_{int(datetime.now().timestamp())}",
        "user_id": user_id,
        "symbol": request.symbol,
        "name": request.name,
        "conditions": conditions,
        "notification_channels": request.notification_channels,
        "custom_message": request.custom_message or f"Alert triggered for {request.symbol}",
        "is_active": True,
        "created_at": datetime.now().isoformat(),
    }

    return alert_data


@router.post("/expanded/evaluate", response_model=dict)
async def evaluate_alerts(
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(...),
):
    """
    Evaluate all active alerts against current market data.
    """
    from app.services.alerts_expansion_service import AlertsExpansionService
    from app.services.yfinance_service import YFinanceService

    # Extract user ID from token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    _user_id = payload["sub"]

    # Get user's active alerts (placeholder - would query database)
    alerts = []

    # Get current market data for user's watchlist
    yfinance = YFinanceService()
    current_data = {}

    try:
        # Get quotes for all symbols in alerts
        symbols = list(set(a.get("symbol") for a in alerts if a.get("symbol")))
        for symbol in symbols:
            try:
                quote = await yfinance.get_quote(symbol)
                current_data[symbol] = {
                    "price": quote.price,
                    "percent_change": getattr(quote, "change_percent", 0),
                }
            except Exception:
                pass
    finally:
        await yfinance.close()

    # Evaluate alerts
    alert_service = AlertsExpansionService()
    results = await alert_service.evaluate_alerts(alerts, current_data)

    return {
        "evaluated_at": datetime.now().isoformat(),
        "results": [
            {
                "alert_id": r.alert_id,
                "symbol": r.symbol,
                "triggered": r.triggered,
                "triggered_conditions": r.triggered_conditions,
                "current_values": r.current_values,
            }
            for r in results
        ],
    }

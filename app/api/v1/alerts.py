"""
Alert API routes.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Alert
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

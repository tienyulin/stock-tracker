"""
Portfolio Health Score API endpoints.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.models.portfolio_health import PortfolioHealthScore, HealthScoreAlert
from app.services.portfolio_health_service import PortfolioHealthService

router = APIRouter(prefix="/portfolio/health", tags=["portfolio_health"])


class HealthScoreResponse(BaseModel):
    score: float
    diversification_score: float
    risk_score: float
    performance_score: float
    trend_score: float
    calculated_at: datetime

    class Config:
        from_attributes = True


class HealthScoreHistoryItem(BaseModel):
    date: datetime
    score: float
    diversification_score: float
    risk_score: float
    performance_score: float
    trend_score: float

    class Config:
        from_attributes = True


class HealthScoreHistoryResponse(BaseModel):
    history: list[HealthScoreHistoryItem]

    class Config:
        from_attributes = True


class HealthScoreAlertResponse(BaseModel):
    threshold: float
    current_score: float
    triggered: bool

    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    threshold: float


class AlertResponse(BaseModel):
    id: uuid.UUID
    threshold: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/score", response_model=HealthScoreResponse)
def get_health_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current portfolio health score with breakdown."""
    service = PortfolioHealthService(db, current_user.id)
    score_data = service.calculate_health_score()

    # Save to history
    service.save_health_score(score_data)

    return HealthScoreResponse(
        score=score_data["score"],
        diversification_score=score_data["diversification_score"],
        risk_score=score_data["risk_score"],
        performance_score=score_data["performance_score"],
        trend_score=score_data["trend_score"],
        calculated_at=score_data["calculated_at"]
    )


@router.get("/history", response_model=HealthScoreHistoryResponse)
def get_health_history(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get historical portfolio health scores."""
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")

    service = PortfolioHealthService(db, current_user.id)
    scores = service.get_health_history(days)

    history = [
        HealthScoreHistoryItem(
            date=s.calculated_at,
            score=s.score,
            diversification_score=s.diversification_score,
            risk_score=s.risk_score,
            performance_score=s.performance_score,
            trend_score=s.trend_score
        )
        for s in scores
    ]

    return HealthScoreHistoryResponse(history=history)


@router.post("/alerts", response_model=AlertResponse)
def create_health_alert(
    alert: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a health score alert (triggers when score drops below threshold)."""
    if alert.threshold < 0 or alert.threshold > 100:
        raise HTTPException(status_code=400, detail="Threshold must be between 0 and 100")

    db_alert = HealthScoreAlert(
        user_id=current_user.id,
        threshold=alert.threshold,
        is_active=True
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)

    return AlertResponse(
        id=db_alert.id,
        threshold=db_alert.threshold,
        is_active=db_alert.is_active,
        created_at=db_alert.created_at
    )


@router.get("/alerts", response_model=list[AlertResponse])
def get_health_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all health score alerts for current user."""
    alerts = db.query(HealthScoreAlert).filter(
        HealthScoreAlert.user_id == current_user.id
    ).order_by(HealthScoreAlert.created_at.desc()).all()

    return [
        AlertResponse(
            id=a.id,
            threshold=a.threshold,
            is_active=a.is_active,
            created_at=a.created_at
        )
        for a in alerts
    ]


@router.delete("/alerts/{alert_id}")
def delete_health_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a health score alert."""
    alert = db.query(HealthScoreAlert).filter(
        HealthScoreAlert.id == alert_id,
        HealthScoreAlert.user_id == current_user.id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    db.delete(alert)
    db.commit()

    return {"message": "Alert deleted successfully"}


@router.get("/alerts/check", response_model=list[HealthScoreAlertResponse])
def check_health_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if any alerts should be triggered with current score."""
    service = PortfolioHealthService(db, current_user.id)
    current_score_data = service.calculate_health_score()
    current_score = current_score_data["score"]

    alerts = db.query(HealthScoreAlert).filter(
        HealthScoreAlert.user_id == current_user.id,
        HealthScoreAlert.is_active.is_(True)
    ).all()

    return [
        HealthScoreAlertResponse(
            threshold=a.threshold,
            current_score=current_score,
            triggered=current_score < a.threshold
        )
        for a in alerts
    ]

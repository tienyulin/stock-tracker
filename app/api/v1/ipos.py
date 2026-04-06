"""
IPO API routes.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.models import User
from app.schemas.ipo_schemas import (
    IPOAlertCreate,
    IPOAlertResponse,
    IPOAnalysisResponse,
    IPOCalendarResponse,
    IPOCreate,
    IPOResponse,
    IPOUpdate,
)
from app.services.ipo_service import IPOService, IPOCalendarService, IPOAlertService

router = APIRouter(prefix="/ipos", tags=["ipos"])
logger = logging.getLogger(__name__)


def _to_response(ipo) -> IPOResponse:
    return IPOResponse(
        id=str(ipo.id),
        user_id=str(ipo.user_id),
        company_name=ipo.company_name,
        ticker=ipo.ticker,
        exchange=ipo.exchange,
        sector=ipo.sector,
        industry=ipo.industry,
        ipo_price_min=ipo.ipo_price_min,
        ipo_price_max=ipo.ipo_price_max,
        final_ipo_price=ipo.final_ipo_price,
        shares_offered=ipo.shares_offered,
        lot_size=ipo.lot_size,
        oversubscription_ratio=ipo.oversubscription_ratio,
        application_deadline=ipo.application_deadline,
        listing_date=ipo.listing_date,
        first_trading_date=ipo.first_trading_date,
        underwriter=ipo.underwriter,
        status=ipo.status,
        estimated_market_cap=ipo.estimated_market_cap,
        raising_amount=ipo.raising_amount,
        notes=ipo.notes,
        is_active=ipo.is_active,
        created_at=ipo.created_at,
        updated_at=ipo.updated_at,
    )


# ─── IPO Management ────────────────────────────────────────────────────────────

@router.get("/", response_model=list[IPOResponse])
async def list_ipos(
    status: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    upcoming_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[IPOResponse]:
    """List all IPO records for the user."""
    service = IPOService(db)
    ipos = service.list_ipos(
        str(current_user.id),
        status=status,
        sector=sector,
        upcoming_only=upcoming_only,
    )
    return [_to_response(ipo) for ipo in ipos]


@router.post("/", response_model=IPOResponse, status_code=201)
async def create_ipo(
    data: IPOCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IPOResponse:
    """Create a new IPO record."""
    service = IPOService(db)
    ipo = service.create_ipo(str(current_user.id), data.model_dump())
    return _to_response(ipo)


@router.get("/upcoming", response_model=list[IPOResponse])
async def get_upcoming_ipos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[IPOResponse]:
    """Get upcoming IPOs."""
    service = IPOService(db)
    ipos = service.get_upcoming_ipos(str(current_user.id))
    return [_to_response(ipo) for ipo in ipos]


@router.get("/{ipo_id}", response_model=IPOResponse)
async def get_ipo(
    ipo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IPOResponse:
    """Get a single IPO record."""
    service = IPOService(db)
    ipo = service.get_ipo(ipo_id, str(current_user.id))
    if not ipo:
        raise HTTPException(status_code=404, detail="IPO not found")
    return _to_response(ipo)


@router.put("/{ipo_id}", response_model=IPOResponse)
async def update_ipo(
    ipo_id: str,
    data: IPOUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IPOResponse:
    """Update an IPO record."""
    service = IPOService(db)
    ipo = service.update_ipo(ipo_id, str(current_user.id), data.model_dump(exclude_unset=True))
    if not ipo:
        raise HTTPException(status_code=404, detail="IPO not found")
    return _to_response(ipo)


@router.delete("/{ipo_id}", status_code=204)
async def delete_ipo(
    ipo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an IPO record."""
    service = IPOService(db)
    deleted = service.delete_ipo(ipo_id, str(current_user.id))
    if not deleted:
        raise HTTPException(status_code=404, detail="IPO not found")


# ─── Analysis & Performance ───────────────────────────────────────────────────

@router.get("/analysis/{ipo_id}", response_model=IPOAnalysisResponse)
async def get_ipo_analysis(
    ipo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IPOAnalysisResponse:
    """Get IPO analysis report."""
    service = IPOService(db)
    analysis = service.get_ipo_analysis(ipo_id, str(current_user.id))
    if not analysis:
        raise HTTPException(status_code=404, detail="IPO not found")
    return IPOAnalysisResponse(**analysis)


@router.get("/performance/{ipo_id}")
async def get_ipo_performance(
    ipo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get IPO post-listing performance."""
    service = IPOService(db)
    perf = service.get_ipo_performance(ipo_id, str(current_user.id))
    if not perf:
        raise HTTPException(status_code=404, detail="IPO not found")
    return perf


# ─── Calendar ──────────────────────────────────────────────────────────────────

@router.get("/calendar", response_model=IPOCalendarResponse)
async def get_ipo_calendar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IPOCalendarResponse:
    """Get IPO calendar overview."""
    service = IPOCalendarService(db)
    return service.get_calendar(str(current_user.id))


@router.get("/deadlines", response_model=list[dict])
async def get_upcoming_deadlines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Get upcoming IPO application deadlines."""
    service = IPOCalendarService(db)
    return service.get_upcoming_deadlines(str(current_user.id))


@router.get("/stats/first-day", response_model=dict)
async def get_first_day_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get first-day performance statistics."""
    service = IPOCalendarService(db)
    return service.get_first_day_stats(str(current_user.id))


# ─── Alerts ───────────────────────────────────────────────────────────────────

@router.get("/alerts", response_model=list[IPOAlertResponse])
async def list_alerts(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[IPOAlertResponse]:
    """List IPO alerts."""
    service = IPOAlertService(db)
    alerts = service.get_alerts(str(current_user.id), active_only=active_only)
    return [
        IPOAlertResponse(
            id=str(a.id),
            user_id=str(a.user_id),
            ipo_id=str(a.ipo_id),
            alert_type=a.alert_type,
            is_active=a.is_active,
            triggered_at=a.triggered_at,
            message=a.message,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@router.post("/alerts", response_model=IPOAlertResponse, status_code=201)
async def create_alert(
    data: IPOAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IPOAlertResponse:
    """Create an IPO alert."""
    service = IPOAlertService(db)
    alert = service.create_alert(str(current_user.id), data.model_dump())
    return IPOAlertResponse(
        id=str(alert.id),
        user_id=str(alert.user_id),
        ipo_id=str(alert.ipo_id),
        alert_type=alert.alert_type,
        is_active=alert.is_active,
        triggered_at=alert.triggered_at,
        message=alert.message,
        created_at=alert.created_at,
    )


@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an IPO alert."""
    service = IPOAlertService(db)
    deleted = service.delete_alert(alert_id, str(current_user.id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")

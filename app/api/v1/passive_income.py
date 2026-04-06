"""
Passive Income Tracker API routes.

Provides endpoints for tracking all passive income sources
(dividends, rental, interest, royalties, pension, etc.) and FIRE progress.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.models.passive_income import (
    FireGoal,
    PassiveIncomeRecord,
    PassiveIncomeSource,
)
from app.schemas.schemas import (
    FireGoalUpsert,
    FireGoalResponse,
    FireProgressResponse,
    PassiveIncomeDashboardResponse,
    PassiveIncomeMonthlySummary,
    PassiveIncomeAnnualSummary,
    PassiveIncomeRecordCreate,
    PassiveIncomeRecordResponse,
    PassiveIncomeSourceCreate,
    PassiveIncomeSourceResponse,
    PassiveIncomeSourceUpdate,
)
from app.services.passive_income_service import PassiveIncomeService

router = APIRouter(prefix="/passive-income", tags=["passive-income"])
logger = logging.getLogger(__name__)


# ─── Sources ──────────────────────────────────────────────────────────────────

@router.post("/sources", response_model=PassiveIncomeSourceResponse, status_code=201)
async def create_source(
    payload: PassiveIncomeSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PassiveIncomeSourceResponse:
    """Create a new passive income source."""
    service = PassiveIncomeService(db)
    source = service.create_source(
        user_id=current_user.id,
        name=payload.name,
        source_type=payload.source_type,
        description=payload.description,
        currency=payload.currency,
        expected_monthly_income=payload.expected_monthly_income,
        expected_annual_income=payload.expected_annual_income,
        yield_on_cost=payload.yield_on_cost,
        start_date=payload.start_date,
        notes=payload.notes,
    )
    return PassiveIncomeSourceResponse.model_validate(source)


@router.get("/sources", response_model=list[PassiveIncomeSourceResponse])
async def list_sources(
    active_only: bool = Query(True, description="Show only active sources"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PassiveIncomeSourceResponse]:
    """List all passive income sources for the current user."""
    service = PassiveIncomeService(db)
    sources = service.get_sources(current_user.id, active_only=active_only)
    return [PassiveIncomeSourceResponse.model_validate(s) for s in sources]


@router.get("/sources/{source_id}", response_model=PassiveIncomeSourceResponse)
async def get_source(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PassiveIncomeSourceResponse:
    """Get a specific passive income source."""
    from uuid import UUID
    try:
        sid = UUID(source_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid source ID format")
    service = PassiveIncomeService(db)
    source = service.get_source(current_user.id, sid)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return PassiveIncomeSourceResponse.model_validate(source)


@router.patch("/sources/{source_id}", response_model=PassiveIncomeSourceResponse)
async def update_source(
    source_id: str,
    payload: PassiveIncomeSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PassiveIncomeSourceResponse:
    """Update a passive income source."""
    from uuid import UUID
    try:
        sid = UUID(source_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid source ID format")
    service = PassiveIncomeService(db)
    updates = payload.model_dump(exclude_unset=True)
    source = service.update_source(sid, current_user.id, **updates)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return PassiveIncomeSourceResponse.model_validate(source)


@router.delete("/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a passive income source."""
    from uuid import UUID
    try:
        sid = UUID(source_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid source ID format")
    service = PassiveIncomeService(db)
    if not service.delete_source(current_user.id, sid):
        raise HTTPException(status_code=404, detail="Source not found")


# ─── Records ───────────────────────────────────────────────────────────────────

@router.post("/records", response_model=PassiveIncomeRecordResponse, status_code=201)
async def add_record(
    payload: PassiveIncomeRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PassiveIncomeRecordResponse:
    """Add a passive income payment record."""
    service = PassiveIncomeService(db)
    # Verify source belongs to user
    source = service.get_source(current_user.id, payload.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    record = service.add_record(
        user_id=current_user.id,
        source_id=payload.source_id,
        amount=payload.amount,
        record_date=payload.record_date,
        currency=payload.currency,
        record_type=payload.record_type,
        notes=payload.notes,
    )
    return PassiveIncomeRecordResponse.model_validate(record)


@router.get("/records", response_model=list[PassiveIncomeRecordResponse])
async def list_records(
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PassiveIncomeRecordResponse]:
    """List passive income records."""
    from uuid import UUID
    sid = None
    if source_id:
        try:
            sid = UUID(source_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid source ID format")
    service = PassiveIncomeService(db)
    records = service.get_records(
        current_user.id,
        source_id=sid,
        start_date=start_date,
        end_date=end_date,
    )
    return [PassiveIncomeRecordResponse.model_validate(r) for r in records[:limit]]


# ─── Summaries ─────────────────────────────────────────────────────────────────

@router.get("/summary/monthly", response_model=PassiveIncomeMonthlySummary)
async def get_monthly_summary(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PassiveIncomeMonthlySummary:
    """Get monthly passive income summary."""
    service = PassiveIncomeService(db)
    return service.get_monthly_summary(current_user.id, year, month)


@router.get("/summary/annual", response_model=PassiveIncomeAnnualSummary)
async def get_annual_summary(
    year: int = Query(..., ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PassiveIncomeAnnualSummary:
    """Get annual passive income summary (12-month breakdown)."""
    service = PassiveIncomeService(db)
    return service.get_annual_summary(current_user.id, year)


# ─── FIRE ──────────────────────────────────────────────────────────────────────

@router.get("/fire", response_model=FireProgressResponse)
async def get_fire_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FireProgressResponse:
    """Get FIRE progress dashboard data."""
    service = PassiveIncomeService(db)
    progress = service.get_fire_progress(current_user.id)
    if not progress:
        raise HTTPException(status_code=404, detail="No FIRE goal set. Please set one first.")
    return FireProgressResponse(**progress)


@router.post("/fire", response_model=FireGoalResponse)
async def upsert_fire_goal(
    payload: FireGoalUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FireGoalResponse:
    """Create or update a FIRE goal."""
    service = PassiveIncomeService(db)
    goal = service.upsert_fire_goal(
        user_id=current_user.id,
        target_annual_income=payload.target_annual_income,
        monthly_expenses=payload.monthly_expenses,
        target_date=payload.target_date,
        currency=payload.currency,
    )
    return FireGoalResponse.model_validate(goal)


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=PassiveIncomeDashboardResponse)
async def get_dashboard(
    year: int = Query(default=datetime.utcnow().year, ge=2000, le=2100),
    month: int = Query(default=datetime.utcnow().month, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PassiveIncomeDashboardResponse:
    """Full passive income dashboard: sources + summaries + FIRE progress."""
    service = PassiveIncomeService(db)
    sources = service.get_sources(current_user.id, active_only=True)
    monthly = service.get_monthly_summary(current_user.id, year, month)
    annual = service.get_annual_summary(current_user.id, year)
    fire = service.get_fire_progress(current_user.id)
    return PassiveIncomeDashboardResponse(
        sources=[PassiveIncomeSourceResponse.model_validate(s) for s in sources],
        monthly_summary=PassiveIncomeMonthlySummary(**monthly),
        annual_summary=PassiveIncomeAnnualSummary(**annual),
        fire_progress=FireProgressResponse(**fire) if fire else None,
    )

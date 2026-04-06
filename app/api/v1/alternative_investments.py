"""
Alternative Investments API routes.

Provides endpoints for tracking private equity, REITs, hedge funds,
and other alternative investments.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models import User
from app.models.alternative_investments import AlternativeInvestment
from app.schemas.schemas import (
    AlternativeInvestmentCreate,
    AlternativeInvestmentResponse,
    AlternativeInvestmentUpdate,
    AlternativeInvestmentsSummaryResponse,
    LiquidityAnalysisResponse,
    NAVHistoryResponse,
    NAVUpdate,
    REITQuoteResponse,
)
from app.services.alternative_investment_service import AlternativeInvestmentService

router = APIRouter(prefix="/alternative-investments", tags=["alternative-investments"])
logger = logging.getLogger(__name__)


def _to_response(inv: AlternativeInvestment) -> AlternativeInvestmentResponse:
    """Convert model to response with computed fields."""
    current_val = inv.current_value or inv.cost_basis or 0
    gain = current_val - (inv.cost_basis or 0)
    gain_pct = (gain / inv.cost_basis * 100) if inv.cost_basis else None
    return AlternativeInvestmentResponse(
        id=inv.id,
        name=inv.name,
        investment_type=inv.investment_type,
        ticker=inv.ticker,
        liquidity=inv.liquidity,
        cost_basis=inv.cost_basis or 0,
        currency=inv.currency,
        purchase_date=inv.purchase_date,
        shares_units=inv.shares_units,
        committed_capital=inv.committed_capital,
        deployed_capital=inv.deployed_capital,
        current_nav_per_share=inv.current_nav_per_share,
        current_value=inv.current_value,
        current_price=inv.current_price,
        rental_income_ytd=inv.rental_income_ytd,
        occupancy_rate=inv.occupancy_rate,
        unrealized_gain=round(gain, 2) if gain else None,
        unrealized_gain_percent=round(gain_pct, 2) if gain_pct else None,
        notes=inv.notes,
        is_active=inv.is_active,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
    )


# ─── Holdings ─────────────────────────────────────────────────────────────────

@router.get("/summary", response_model=AlternativeInvestmentsSummaryResponse)
async def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlternativeInvestmentsSummaryResponse:
    """Get alternative investments summary dashboard."""
    service = AlternativeInvestmentService(db)
    summary = service.get_summary(current_user.id)
    return AlternativeInvestmentsSummaryResponse(**summary)


@router.get("/holdings", response_model=list[AlternativeInvestmentResponse])
async def list_holdings(
    investment_type: Optional[str] = Query(None, description="Filter by type"),
    liquidity: Optional[str] = Query(None, description="Filter by liquidity"),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AlternativeInvestmentResponse]:
    """List all alternative investment holdings."""
    service = AlternativeInvestmentService(db)
    investments = service.get_investments(
        current_user.id,
        investment_type=investment_type,
        liquidity=liquidity,
        active_only=active_only,
    )
    return [_to_response(inv) for inv in investments]


@router.post(
    "/holdings",
    response_model=AlternativeInvestmentResponse,
    status_code=201,
)
async def create_holding(
    payload: AlternativeInvestmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlternativeInvestmentResponse:
    """Create a new alternative investment holding."""
    service = AlternativeInvestmentService(db)
    inv = service.create_investment(
        user_id=current_user.id,
        name=payload.name,
        investment_type=payload.investment_type,
        ticker=payload.ticker,
        liquidity=payload.liquidity,
        cost_basis=payload.cost_basis,
        currency=payload.currency,
        purchase_date=payload.purchase_date,
        shares_units=payload.shares_units,
        committed_capital=payload.committed_capital,
        deployed_capital=payload.deployed_capital,
        current_nav_per_share=payload.current_nav_per_share,
        current_value=payload.current_value,
        current_price=payload.current_price,
        rental_income_ytd=payload.rental_income_ytd,
        occupancy_rate=payload.occupancy_rate,
        notes=payload.notes,
    )
    return _to_response(inv)


@router.get("/holdings/{investment_id}", response_model=AlternativeInvestmentResponse)
async def get_holding(
    investment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlternativeInvestmentResponse:
    """Get a specific alternative investment."""
    from uuid import UUID
    service = AlternativeInvestmentService(db)
    inv = service.get_investment(UUID(investment_id), current_user.id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
    return _to_response(inv)


@router.put("/holdings/{investment_id}", response_model=AlternativeInvestmentResponse)
async def update_holding(
    investment_id: str,
    payload: AlternativeInvestmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlternativeInvestmentResponse:
    """Update an alternative investment holding."""
    from uuid import UUID
    service = AlternativeInvestmentService(db)
    kwargs = payload.model_dump(exclude_unset=True)
    inv = service.update_investment(UUID(investment_id), current_user.id, **kwargs)
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
    return _to_response(inv)


@router.delete("/holdings/{investment_id}", status_code=204)
async def delete_holding(
    investment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete (deactivate) an alternative investment holding."""
    from uuid import UUID
    service = AlternativeInvestmentService(db)
    deleted = service.delete_investment(UUID(investment_id), current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Investment not found")


# ─── NAV ─────────────────────────────────────────────────────────────────────

@router.post(
    "/holdings/{investment_id}/nav",
    response_model=NAVHistoryResponse,
    status_code=201,
)
async def add_nav_record(
    investment_id: str,
    payload: NAVUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NAVHistoryResponse:
    """Add a NAV record to a private fund."""
    from uuid import UUID
    service = AlternativeInvestmentService(db)
    nav = service.add_nav_record(
        investment_id=UUID(investment_id),
        user_id=current_user.id,
        nav_date=payload.nav_date,
        nav_per_share=payload.nav_per_share,
        total_value=payload.total_value,
        notes=payload.notes,
    )
    if not nav:
        raise HTTPException(status_code=404, detail="Investment not found")
    return NAVHistoryResponse.model_validate(nav)


@router.get(
    "/holdings/{investment_id}/nav",
    response_model=list[NAVHistoryResponse],
)
async def get_nav_history(
    investment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NAVHistoryResponse]:
    """Get NAV history for a fund."""
    from uuid import UUID
    service = AlternativeInvestmentService(db)
    records = service.get_nav_history(UUID(investment_id), current_user.id)
    return [NAVHistoryResponse.model_validate(r) for r in records]


# ─── REITs ─────────────────────────────────────────────────────────────────────

@router.get("/reits/{ticker}", response_model=REITQuoteResponse)
async def get_reit_quote(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> REITQuoteResponse:
    """Get real-time REIT quote from market data."""
    service = AlternativeInvestmentService(db)
    quote = service.get_reits_quote(ticker.upper())
    if not quote:
        raise HTTPException(status_code=404, detail=f"Could not fetch quote for {ticker}")
    return REITQuoteResponse(**quote)


# ─── Liquidity Analysis ───────────────────────────────────────────────────────

@router.get("/liquidity-analysis", response_model=LiquidityAnalysisResponse)
async def get_liquidity_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LiquidityAnalysisResponse:
    """Get liquidity analysis of alternative investments."""
    service = AlternativeInvestmentService(db)
    summary = service.get_summary(current_user.id)
    return LiquidityAnalysisResponse(**summary["liquidity_analysis"])

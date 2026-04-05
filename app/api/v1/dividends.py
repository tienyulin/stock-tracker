"""
Dividend Growth Tracker API routes.

Provides endpoints for tracking dividend income, yield analytics,
and dividend growth trends.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models import User, DividendPayment, DividendHolding, ExDividendCalendar
from app.schemas.schemas import (
    DividendPaymentCreate,
    DividendPaymentResponse,
    DividendHoldingUpdate,
    DividendHoldingResponse,
    DividendDashboardResponse,
    DividendCalendarEntry,
    DividendGrowthResponse,
)

router = APIRouter(prefix="/dividends", tags=["dividends"])
logger = logging.getLogger(__name__)


def calculate_yield(current_price: float, annual_dividend: float) -> float:
    """Calculate dividend yield percentage."""
    if current_price <= 0:
        return 0.0
    return (annual_dividend / current_price) * 100


def calculate_yield_on_cost(cost_basis: float, shares: float, annual_dividend: float) -> float:
    """Calculate yield on cost percentage."""
    if cost_basis <= 0 or shares <= 0:
        return 0.0
    total_annual = annual_dividend * shares
    return (total_annual / cost_basis) * 100


# ============ Dividend Payments ============

@router.get("/payments", response_model=list[DividendPaymentResponse])
async def get_dividend_payments(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DividendPaymentResponse]:
    """
    Get dividend payment history for the current user.

    Args:
        symbol: Optional symbol filter
        start_date: Filter payments from this date
        end_date: Filter payments until this date
        limit: Maximum number of records to return

    Returns:
        List of dividend payment records
    """
    query = db.query(DividendPayment).filter(DividendPayment.user_id == current_user.id)

    if symbol:
        query = query.filter(DividendPayment.symbol == symbol.upper())
    if start_date:
        query = query.filter(DividendPayment.payment_date >= start_date)
    if end_date:
        query = query.filter(DividendPayment.payment_date <= end_date)

    payments = query.order_by(desc(DividendPayment.payment_date)).limit(limit).all()
    return [DividendPaymentResponse.model_validate(p) for p in payments]


@router.post("/payments", response_model=DividendPaymentResponse)
async def create_dividend_payment(
    payment: DividendPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DividendPaymentResponse:
    """
    Record a new dividend payment.

    Args:
        payment: Dividend payment details

    Returns:
        Created dividend payment record
    """
    # Auto-calculate total amount if not provided
    total_amount = payment.total_amount or (payment.amount_per_share * payment.shares_owned)

    db_payment = DividendPayment(
        user_id=current_user.id,
        symbol=payment.symbol.upper(),
        ex_dividend_date=payment.ex_dividend_date,
        payment_date=payment.payment_date,
        amount_per_share=payment.amount_per_share,
        shares_owned=payment.shares_owned,
        total_amount=total_amount,
        currency=payment.currency,
    )

    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)

    logger.info(f"Dividend payment recorded: {current_user.id} | {payment.symbol} | ${total_amount}")
    return DividendPaymentResponse.model_validate(db_payment)


@router.delete("/payments/{payment_id}")
async def delete_dividend_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete a dividend payment record."""
    payment = db.query(DividendPayment).filter(
        DividendPayment.id == payment_id,
        DividendPayment.user_id == current_user.id
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Dividend payment not found")

    db.delete(payment)
    db.commit()

    return {"message": "Dividend payment deleted successfully"}


# ============ Dividend Holdings ============

@router.get("/holdings", response_model=list[DividendHoldingResponse])
async def get_dividend_holdings(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DividendHoldingResponse]:
    """
    Get dividend tracking info for user's holdings.

    Args:
        symbol: Optional symbol filter

    Returns:
        List of dividend holding records
    """
    query = db.query(DividendHolding).filter(DividendHolding.user_id == current_user.id)

    if symbol:
        query = query.filter(DividendHolding.symbol == symbol.upper())

    holdings = query.order_by(DividendHolding.symbol).all()
    return [DividendHoldingResponse.model_validate(h) for h in holdings]


@router.put("/holdings/{symbol}", response_model=DividendHoldingResponse)
async def update_dividend_holding(
    symbol: str,
    update: DividendHoldingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DividendHoldingResponse:
    """
    Create or update dividend holding information for a symbol.

    Args:
        symbol: Stock symbol
        update: Updated dividend data

    Returns:
        Updated dividend holding record
    """
    holding = db.query(DividendHolding).filter(
        DividendHolding.user_id == current_user.id,
        DividendHolding.symbol == symbol.upper()
    ).first()

    if not holding:
        # Create new holding
        holding = DividendHolding(
            user_id=current_user.id,
            symbol=symbol.upper(),
            shares_owned=update.shares_owned or 0,
            cost_basis=update.cost_basis or 0,
            annual_dividend=update.annual_dividend or 0,
        )
        db.add(holding)
    else:
        # Update existing
        if update.shares_owned is not None:
            holding.shares_owned = update.shares_owned
        if update.cost_basis is not None:
            holding.cost_basis = update.cost_basis
        if update.annual_dividend is not None:
            holding.annual_dividend = update.annual_dividend

    # Recalculate yields
    if holding.cost_basis > 0 and holding.shares_owned > 0 and holding.annual_dividend > 0:
        total_cost = holding.cost_basis * holding.shares_owned
        total_annual = holding.annual_dividend * holding.shares_owned
        holding.yield_on_cost = (total_annual / total_cost) * 100 if total_cost > 0 else 0

    db.commit()
    db.refresh(holding)

    logger.info(f"Dividend holding updated: {current_user.id} | {symbol}")
    return DividendHoldingResponse.model_validate(holding)


@router.delete("/holdings/{symbol}")
async def delete_dividend_holding(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete a dividend holding record."""
    holding = db.query(DividendHolding).filter(
        DividendHolding.user_id == current_user.id,
        DividendHolding.symbol == symbol.upper()
    ).first()

    if not holding:
        raise HTTPException(status_code=404, detail="Dividend holding not found")

    db.delete(holding)
    db.commit()

    return {"message": "Dividend holding deleted successfully"}


# ============ Dividend Dashboard ============

@router.get("/dashboard", response_model=DividendDashboardResponse)
async def get_dividend_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DividendDashboardResponse:
    """
    Get dividend dashboard with summary statistics.

    Returns:
        Dividend dashboard with totals and recent/upcoming items
    """
    now = datetime.now()
    current_year = now.year
    last_year = current_year - 1

    # Calculate totals
    total_dividends = db.query(func.sum(DividendPayment.total_amount)).filter(
        DividendPayment.user_id == current_user.id
    ).scalar() or 0.0

    dividends_this_year = db.query(func.sum(DividendPayment.total_amount)).filter(
        DividendPayment.user_id == current_user.id,
        func.extract('year', DividendPayment.payment_date) == current_year
    ).scalar() or 0.0

    dividends_last_year = db.query(func.sum(DividendPayment.total_amount)).filter(
        DividendPayment.user_id == current_user.id,
        func.extract('year', DividendPayment.payment_date) == last_year
    ).scalar() or 0.0

    # YoY growth
    yoy_growth = ((dividends_this_year - dividends_last_year) / dividends_last_year * 100) if dividends_last_year > 0 else 0.0

    # Get holdings for portfolio yield calculation
    holdings = db.query(DividendHolding).filter(DividendHolding.user_id == current_user.id).all()
    total_cost_basis = sum(h.cost_basis * h.shares_owned for h in holdings)
    total_annual_dividend = sum(h.annual_dividend * h.shares_owned for h in holdings)

    portfolio_yield = calculate_yield(total_cost_basis / sum(h.shares_owned for h in holdings) if holdings else 1, total_annual_dividend / len(holdings) if holdings else 0)

    avg_yoc = sum(h.yield_on_cost for h in holdings) / len(holdings) if holdings else 0.0

    # Recent payments
    recent = db.query(DividendPayment).filter(
        DividendPayment.user_id == current_user.id
    ).order_by(desc(DividendPayment.payment_date)).limit(10).all()

    # Upcoming ex-dividends
    upcoming = db.query(ExDividendCalendar).filter(
        ExDividendCalendar.user_id == current_user.id,
        ExDividendCalendar.ex_dividend_date >= now,
        ExDividendCalendar.is_upcoming == True
    ).order_by(ExDividendCalendar.ex_dividend_date).limit(10).all()

    return DividendDashboardResponse(
        total_dividends_received=float(total_dividends),
        dividends_this_year=float(dividends_this_year),
        dividends_last_year=float(dividends_last_year),
        year_over_year_growth=round(yoy_growth, 2),
        portfolio_dividend_yield=round(portfolio_yield, 2),
        yield_on_cost=round(avg_yoc, 2),
        recent_payments=[DividendPaymentResponse.model_validate(p) for p in recent],
        upcoming_ex_dividends=[
            DividendCalendarEntry(
                symbol=u.symbol,
                ex_dividend_date=u.ex_dividend_date,
                payment_date=u.payment_date,
                amount_per_share=u.amount_per_share
            ) for u in upcoming
        ]
    )


# ============ Dividend Growth Analytics ============

@router.get("/growth/{symbol}", response_model=DividendGrowthResponse)
async def get_dividend_growth(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DividendGrowthResponse:
    """
    Get dividend growth analytics for a specific symbol.

    Args:
        symbol: Stock symbol

    Returns:
        Dividend growth analytics
    """
    holding = db.query(DividendHolding).filter(
        DividendHolding.user_id == current_user.id,
        DividendHolding.symbol == symbol.upper()
    ).first()

    if not holding:
        raise HTTPException(status_code=404, detail=f"No dividend data for {symbol}")

    # Get historical payments to calculate growth
    payments = db.query(DividendPayment).filter(
        DividendPayment.user_id == current_user.id,
        DividendPayment.symbol == symbol.upper()
    ).order_by(DividendPayment.payment_date).all()

    current_yield = calculate_yield(holding.shares_owned * 100, holding.annual_dividend)  # Simplified

    return DividendGrowthResponse(
        symbol=symbol.upper(),
        annual_dividend=holding.annual_dividend,
        previous_annual_dividend=holding.annual_dividend * (1 - holding.dividend_growth_rate / 100) if holding.dividend_growth_rate else holding.annual_dividend,
        dividend_growth_rate=holding.dividend_growth_rate,
        yield_on_cost=holding.yield_on_cost,
        current_yield=current_yield,
        years_of_growth=len(payments) if payments else 0
    )


# ============ Ex-Dividend Calendar ============

@router.get("/calendar", response_model=list[DividendCalendarEntry])
async def get_ex_dividend_calendar(
    days_ahead: int = Query(30, ge=1, le=365, description="Days ahead to look"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DividendCalendarEntry]:
    """
    Get upcoming ex-dividend and payment dates.

    Args:
        days_ahead: Number of days ahead to look

    Returns:
        List of upcoming dividend dates
    """
    now = datetime.now()
    end_date = now + timedelta(days=days_ahead)

    entries = db.query(ExDividendCalendar).filter(
        ExDividendCalendar.user_id == current_user.id,
        ExDividendCalendar.ex_dividend_date >= now,
        ExDividendCalendar.ex_dividend_date <= end_date,
        ExDividendCalendar.is_upcoming == True
    ).order_by(ExDividendCalendar.ex_dividend_date).all()

    return [
        DividendCalendarEntry(
            symbol=e.symbol,
            ex_dividend_date=e.ex_dividend_date,
            payment_date=e.payment_date,
            amount_per_share=e.amount_per_share
        ) for e in entries
    ]


@router.post("/calendar", response_model=DividendCalendarEntry)
async def add_ex_dividend_date(
    entry: DividendCalendarEntry,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DividendCalendarEntry:
    """
    Add an upcoming ex-dividend date to the calendar.

    Args:
        entry: Ex-dividend date details

    Returns:
        Created calendar entry
    """
    db_entry = ExDividendCalendar(
        user_id=current_user.id,
        symbol=entry.symbol.upper(),
        ex_dividend_date=entry.ex_dividend_date,
        payment_date=entry.payment_date,
        amount_per_share=entry.amount_per_share,
        is_upcoming=True
    )

    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    return DividendCalendarEntry(
        symbol=db_entry.symbol,
        ex_dividend_date=db_entry.ex_dividend_date,
        payment_date=db_entry.payment_date,
        amount_per_share=db_entry.amount_per_share
    )


@router.delete("/calendar/{entry_id}")
async def delete_ex_dividend_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete an ex-dividend calendar entry."""
    entry = db.query(ExDividendCalendar).filter(
        ExDividendCalendar.id == entry_id,
        ExDividendCalendar.user_id == current_user.id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Calendar entry not found")

    db.delete(entry)
    db.commit()

    return {"message": "Calendar entry deleted successfully"}

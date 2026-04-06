"""
Cash Flow Forecasting & Liquidity Planning API v1 routes.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.services.cash_flow_service import (
    CashFlowService,
    CashFlowForecastService,
    LiquidityPlanningService,
    EmergencyFundService,
    LargeExpenseService,
)

router = APIRouter(prefix="/cashflow", tags=["Cash Flow"])


# ============== Schemas ==============

class CashFlowEntryCreate(BaseModel):
    entry_type: str  # "income" or "expense"
    category: str
    amount: float
    date: str  # YYYY-MM-DD
    description: Optional[str] = None
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None
    source: Optional[str] = None


class CashFlowEntryResponse(BaseModel):
    id: str
    entry_type: str
    category: str
    amount: float
    date: str
    description: Optional[str] = None
    is_recurring: bool


class MonthlyCashFlowResponse(BaseModel):
    year_month: str
    total_income: float
    total_expense: float
    net_cash_flow: float
    passive_income: float
    active_income: float
    savings_rate: float


class ForecastResponse(BaseModel):
    forecast_months: int
    forecasted_balance: float
    shortfall_months: list[str]
    confidence_score: float


class LiquidityResponse(BaseModel):
    total_liquid_assets: float
    months_of_expenses_covered: float
    liquidity_ratio: float
    high_liquidity: float
    medium_liquidity: float
    low_liquidity: float


class EmergencyFundResponse(BaseModel):
    current_fund: float
    recommended_minimum: float
    recommended_ideal: float
    coverage_months: float
    shortfall: float
    progress_percentage: float
    is_adequate: bool


class EmergencyFundUpdate(BaseModel):
    current_amount: float
    monthly_expenses_estimate: float


class LargeExpenseCreate(BaseModel):
    description: str
    estimated_amount: float
    planned_date: str  # YYYY-MM-DD


class LargeExpenseResponse(BaseModel):
    id: str
    description: str
    estimated_amount: float
    planned_date: str
    months_until: int
    monthly_savings_needed: float
    status: str


# ============== Dependency ==============

def get_cashflow_service(db: Session = Depends(get_db)) -> CashFlowService:
    return CashFlowService(db)


def get_forecast_service(db: Session = Depends(get_db)) -> CashFlowForecastService:
    return CashFlowForecastService(db)


def get_liquidity_service(db: Session = Depends(get_db)) -> LiquidityPlanningService:
    return LiquidityPlanningService(db)


def get_emergency_fund_service(db: Session = Depends(get_db)) -> EmergencyFundService:
    return EmergencyFundService(db)


def get_large_expense_service(db: Session = Depends(get_db)) -> LargeExpenseService:
    return LargeExpenseService(db)


# ============== Endpoints ==============

@router.post("/entry", response_model=CashFlowEntryResponse)
async def create_cashflow_entry(
    request: CashFlowEntryCreate,
    current_user = Depends(get_current_user),
    service: CashFlowService = Depends(get_cashflow_service),
):
    """Create a cash flow entry."""
    entry_date = datetime.strptime(request.date, "%Y-%m-%d").date()
    entry = service.create_entry(
        user_id=current_user.id,
        entry_type=request.entry_type,
        category=request.category,
        amount=request.amount,
        entry_date=entry_date,
        description=request.description,
        is_recurring=request.is_recurring,
        recurring_frequency=request.recurring_frequency,
        source=request.source,
    )
    return CashFlowEntryResponse(
        id=str(entry.id),
        entry_type=entry.entry_type,
        category=entry.category,
        amount=float(entry.amount),
        date=str(entry.date),
        description=entry.description,
        is_recurring=entry.is_recurring,
    )


@router.get("/entries", response_model=list[CashFlowEntryResponse])
async def list_cashflow_entries(
    year_month: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: CashFlowService = Depends(get_cashflow_service),
):
    """List cash flow entries, optionally filtered by month."""
    entries = service.get_entries(current_user.id, year_month=year_month)
    return [
        CashFlowEntryResponse(
            id=str(e.id),
            entry_type=e.entry_type,
            category=e.category,
            amount=float(e.amount),
            date=str(e.date),
            description=e.description,
            is_recurring=e.is_recurring,
        )
        for e in entries
    ]


@router.delete("/entry/{entry_id}")
async def delete_cashflow_entry(
    entry_id: UUID,
    current_user = Depends(get_current_user),
    service: CashFlowService = Depends(get_cashflow_service),
):
    """Delete a cash flow entry."""
    success = service.delete_entry(entry_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "deleted"}


@router.get("/monthly/{year_month}", response_model=MonthlyCashFlowResponse)
async def get_monthly_cashflow(
    year_month: str,
    current_user = Depends(get_current_user),
    service: CashFlowService = Depends(get_cashflow_service),
):
    """Get monthly cash flow summary."""
    result = service.get_monthly_cashflow(current_user.id, year_month)
    return MonthlyCashFlowResponse(**result)


@router.get("/forecast", response_model=ForecastResponse)
async def get_cashflow_forecast(
    months: int = 3,
    current_user = Depends(get_current_user),
    service: CashFlowForecastService = Depends(get_forecast_service),
):
    """Get cash flow forecast for next N months."""
    if months not in (3, 6, 12):
        raise HTTPException(status_code=400, detail="months must be 3, 6, or 12")
    result = service.get_forecast(current_user.id, months=months)
    return ForecastResponse(**result)


@router.get("/liquidity", response_model=LiquidityResponse)
async def get_liquidity_position(
    high_liquidity: float = 0,
    medium_liquidity: float = 0,
    low_liquidity: float = 0,
    current_user = Depends(get_current_user),
    service: LiquidityPlanningService = Depends(get_liquidity_service),
):
    """Get liquidity position."""
    result = service.get_position(
        current_user.id,
        high_liquidity=high_liquidity,
        medium_liquidity=medium_liquidity,
        low_liquidity=low_liquidity,
    )
    return LiquidityResponse(**result)


@router.get("/emergency-fund", response_model=EmergencyFundResponse)
async def get_emergency_fund_status(
    current_user = Depends(get_current_user),
    service: EmergencyFundService = Depends(get_emergency_fund_service),
):
    """Get emergency fund status."""
    result = service.get_status(current_user.id)
    return EmergencyFundResponse(**result)


@router.put("/emergency-fund", response_model=EmergencyFundResponse)
async def update_emergency_fund(
    request: EmergencyFundUpdate,
    current_user = Depends(get_current_user),
    service: EmergencyFundService = Depends(get_emergency_fund_service),
):
    """Create or update emergency fund amount."""
    fund = service.upsert_fund(
        user_id=current_user.id,
        current_amount=request.current_amount,
        monthly_expenses_estimate=request.monthly_expenses_estimate,
    )
    result = service.get_status(current_user.id)
    return EmergencyFundResponse(**result)


@router.post("/large-expense", response_model=LargeExpenseResponse)
async def create_large_expense(
    request: LargeExpenseCreate,
    current_user = Depends(get_current_user),
    service: LargeExpenseService = Depends(get_large_expense_service),
):
    """Create a planned large expense."""
    planned_date = datetime.strptime(request.planned_date, "%Y-%m-%d").date()
    expense = service.create(
        user_id=current_user.id,
        description=request.description,
        estimated_amount=request.estimated_amount,
        planned_date=planned_date,
    )
    return LargeExpenseResponse(
        id=str(expense.id),
        description=expense.description,
        estimated_amount=float(expense.estimated_amount),
        planned_date=str(expense.planned_date),
        months_until=max(0, (expense.planned_date - datetime.utcnow().date()).days // 30),
        monthly_savings_needed=float(expense.monthly_savings_needed),
        status=expense.status,
    )


@router.get("/large-expenses", response_model=list[LargeExpenseResponse])
async def list_large_expenses(
    current_user = Depends(get_current_user),
    service: LargeExpenseService = Depends(get_large_expense_service),
):
    """List planned large expenses."""
    expenses = service.list_expenses(current_user.id)
    return [
        LargeExpenseResponse(
            id=str(e.id),
            description=e.description,
            estimated_amount=float(e.estimated_amount),
            planned_date=str(e.planned_date),
            months_until=max(0, (e.planned_date - datetime.utcnow().date()).days // 30),
            monthly_savings_needed=float(e.monthly_savings_needed),
            status=e.status,
        )
        for e in expenses
    ]

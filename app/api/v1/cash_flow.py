"""
Cash Flow Forecasting & Liquidity Planning API v1 routes.
"""

from typing import Optional
from decimal import Decimal
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/cashflow", tags=["Cash Flow"])


# ============== Schemas ==============

class CashFlowEntryCreate(BaseModel):
    entry_type: str  # "income" or "expense"
    category: str
    amount: float
    date: str
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


class LargeExpenseCreate(BaseModel):
    description: str
    estimated_amount: float
    planned_date: str


class LargeExpenseResponse(BaseModel):
    id: str
    description: str
    estimated_amount: float
    planned_date: str
    months_until: int
    monthly_savings_needed: float
    status: str


# ============== In-memory storage ==============

_cashflow_entries: dict[str, list] = {}  # user_id -> list of entries
_large_expenses: dict[str, list] = {}  # user_id -> list of expenses


def _get_user_entries(user_id: str) -> list:
    if user_id not in _cashflow_entries:
        _cashflow_entries[user_id] = []
    return _cashflow_entries[user_id]


def _calculate_monthly_cashflow(user_id: str, year_month: str) -> dict:
    """Calculate cash flow for a specific month."""
    entries = _get_user_entries(user_id)
    income = Decimal("0")
    expense = Decimal("0")
    passive = Decimal("0")
    active = Decimal("0")
    income_by_cat = {}
    expense_by_cat = {}

    for e in entries:
        if e.get("date", "")[:7] != year_month:
            continue
        amt = Decimal(str(e.get("amount", 0)))
        cat = e.get("category", "other")
        if e.get("entry_type") == "income":
            income += amt
            income_by_cat[cat] = income_by_cat.get(cat, Decimal("0")) + amt
            if cat in ("dividend", "interest", "rental", "other_passive"):
                passive += amt
            else:
                active += amt
        else:
            expense += amt
            expense_by_cat[cat] = expense_by_cat.get(cat, Decimal("0")) + amt

    net = income - expense
    savings_rate = float(income / income * 100) if income > 0 else 0.0

    return {
        "year_month": year_month,
        "total_income": float(income),
        "total_expense": float(expense),
        "net_cash_flow": float(net),
        "passive_income": float(passive),
        "active_income": float(active),
        "income_by_category": {k: float(v) for k, v in income_by_cat.items()},
        "expense_by_category": {k: float(v) for k, v in expense_by_cat.items()},
        "savings_rate": savings_rate,
    }


# ============== Endpoints ==============

@router.post("/entry", response_model=CashFlowEntryResponse)
async def create_cashflow_entry(
    request: CashFlowEntryCreate,
    current_user = Depends(get_current_user),
):
    """Create a cash flow entry."""
    import uuid
    user_id = str(current_user.id)
    entry_id = str(uuid.uuid4())

    entry = {
        "id": entry_id,
        "user_id": user_id,
        "entry_type": request.entry_type,
        "category": request.category,
        "amount": Decimal(str(request.amount)),
        "date": request.date,
        "description": request.description,
        "is_recurring": request.is_recurring,
        "recurring_frequency": request.recurring_frequency,
        "source": request.source,
    }
    _get_user_entries(user_id).append(entry)

    return CashFlowEntryResponse(
        id=entry_id,
        entry_type=request.entry_type,
        category=request.category,
        amount=request.amount,
        date=request.date,
        description=request.description,
        is_recurring=request.is_recurring,
    )


@router.get("/entries", response_model=list[CashFlowEntryResponse])
async def list_cashflow_entries(
    year_month: Optional[str] = None,
    current_user = Depends(get_current_user),
):
    """List cash flow entries, optionally filtered by month."""
    user_id = str(current_user.id)
    entries = _get_user_entries(user_id)

    if year_month:
        entries = [e for e in entries if e.get("date", "").startswith(year_month)]

    return [
        CashFlowEntryResponse(
            id=e["id"],
            entry_type=e["entry_type"],
            category=e["category"],
            amount=float(e["amount"]),
            date=e["date"],
            description=e.get("description"),
            is_recurring=e.get("is_recurring", False),
        )
        for e in sorted(entries, key=lambda x: x["date"], reverse=True)
    ]


@router.get("/monthly/{year_month}", response_model=MonthlyCashFlowResponse)
async def get_monthly_cashflow(
    year_month: str,
    current_user = Depends(get_current_user),
):
    """Get monthly cash flow summary."""
    result = _calculate_monthly_cashflow(str(current_user.id), year_month)
    return MonthlyCashFlowResponse(**result)


@router.get("/forecast", response_model=ForecastResponse)
async def get_cashflow_forecast(
    months: int = 3,
    current_user = Depends(get_current_user),
):
    """Get cash flow forecast for next N months."""
    if months not in (3, 6, 12):
        raise HTTPException(status_code=400, detail="months must be 3, 6, or 12")

    user_id = str(current_user.id)

    # Get average monthly cash flow from last 3 months
    now = datetime.utcnow()
    monthly_flows = []
    for i in range(1, 4):
        ym = (now - timedelta(days=30 * i)).strftime("%Y-%m")
        flow = _calculate_monthly_cashflow(user_id, ym)
        if flow["total_income"] > 0 or flow["total_expense"] > 0:
            monthly_flows.append(flow)

    if not monthly_flows:
        return ForecastResponse(
            forecast_months=months,
            forecasted_balance=0.0,
            shortfall_months=[],
            confidence_score=0.3,
        )

    # Calculate averages
    avg_income = sum(f["total_income"] for f in monthly_flows) / len(monthly_flows)
    avg_expense = sum(f["total_expense"] for f in monthly_flows) / len(monthly_flows)
    avg_net = avg_income - avg_expense

    # Project future months
    forecasted_balance = avg_net * months
    shortfall_months = []

    # Calculate confidence based on consistency
    if len(monthly_flows) >= 2:
        net_values = [f["net_cash_flow"] for f in monthly_flows]
        variance = sum((v - avg_net) ** 2 for v in net_values) / len(net_values)
        std_dev = variance ** 0.5
        confidence = max(0.3, min(0.9, 1.0 - (std_dev / (abs(avg_net) + 1) * 0.1)))
    else:
        confidence = 0.5

    return ForecastResponse(
        forecast_months=months,
        forecasted_balance=float(forecasted_balance),
        shortfall_months=shortfall_months,
        confidence_score=confidence,
    )


@router.get("/liquidity", response_model=LiquidityResponse)
async def get_liquidity_position(
    high_liquidity: float = 0,
    medium_liquidity: float = 0,
    low_liquidity: float = 0,
    current_user = Depends(get_current_user),
):
    """Get liquidity position."""
    user_id = str(current_user.id)

    # Calculate average monthly expenses from recent data
    now = datetime.utcnow()
    total_expense = 0
    count = 0
    for i in range(1, 4):
        ym = (now - timedelta(days=30 * i)).strftime("%Y-%m")
        flow = _calculate_monthly_cashflow(user_id, ym)
        if flow["total_expense"] > 0:
            total_expense += flow["total_expense"]
            count += 1

    avg_monthly_expense = total_expense / count if count > 0 else 1

    total_liquid = high_liquidity + medium_liquidity + low_liquidity
    months_covered = total_liquid / avg_monthly_expense if avg_monthly_expense > 0 else 0
    liquidity_ratio = high_liquidity / avg_monthly_expense if avg_monthly_expense > 0 else 0

    return LiquidityResponse(
        total_liquid_assets=total_liquid,
        months_of_expenses_covered=float(months_covered),
        liquidity_ratio=float(liquidity_ratio),
        high_liquidity=high_liquidity,
        medium_liquidity=medium_liquidity,
        low_liquidity=low_liquidity,
    )


@router.get("/emergency-fund", response_model=EmergencyFundResponse)
async def get_emergency_fund_status(
    current_fund: float = 0,
    monthly_expenses: float = 0,
    current_user = Depends(get_current_user),
):
    """Get emergency fund status."""
    recommended_min = monthly_expenses * 3
    recommended_ideal = monthly_expenses * 6

    coverage = current_fund / monthly_expenses if monthly_expenses > 0 else 0
    shortfall = max(0, recommended_ideal - current_fund)
    progress = min((current_fund / recommended_ideal * 100), 100) if recommended_ideal > 0 else 0

    return EmergencyFundResponse(
        current_fund=current_fund,
        recommended_minimum=recommended_min,
        recommended_ideal=recommended_ideal,
        coverage_months=float(coverage),
        shortfall=float(shortfall),
        progress_percentage=float(progress),
        is_adequate=coverage >= 3,
    )


@router.post("/large-expense", response_model=LargeExpenseResponse)
async def create_large_expense(
    request: LargeExpenseCreate,
    current_user = Depends(get_current_user),
):
    """Create a planned large expense."""
    import uuid
    user_id = str(current_user.id)

    planned_date = datetime.strptime(request.planned_date, "%Y-%m-%d").date()
    months_until = max(0, (planned_date - datetime.utcnow().date()).days // 30)
    monthly_savings_needed = float(request.estimated_amount) / months_until if months_until > 0 else float(request.estimated_amount)

    expense_id = str(uuid.uuid4())
    expense = {
        "id": expense_id,
        "user_id": user_id,
        "description": request.description,
        "estimated_amount": Decimal(str(request.estimated_amount)),
        "planned_date": request.planned_date,
        "months_until": months_until,
        "monthly_savings_needed": Decimal(str(monthly_savings_needed)),
        "status": "planned",
    }

    if user_id not in _large_expenses:
        _large_expenses[user_id] = []
    _large_expenses[user_id].append(expense)

    return LargeExpenseResponse(
        id=expense_id,
        description=request.description,
        estimated_amount=request.estimated_amount,
        planned_date=request.planned_date,
        months_until=months_until,
        monthly_savings_needed=monthly_savings_needed,
        status="planned",
    )


@router.get("/large-expenses", response_model=list[LargeExpenseResponse])
async def list_large_expenses(
    current_user = Depends(get_current_user),
):
    """List planned large expenses."""
    user_id = str(current_user.id)
    expenses = _large_expenses.get(user_id, [])
    return [
        LargeExpenseResponse(
            id=e["id"],
            description=e["description"],
            estimated_amount=float(e["estimated_amount"]),
            planned_date=e["planned_date"],
            months_until=e["months_until"],
            monthly_savings_needed=float(e["monthly_savings_needed"]),
            status=e["status"],
        )
        for e in sorted(expenses, key=lambda x: x["planned_date"])
    ]

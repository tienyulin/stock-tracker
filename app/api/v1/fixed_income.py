"""
Fixed Income API v1 routes: Bonds & Term Deposits.
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.services.fixed_income_service import (
    FixedIncomeService,
    TermDepositService,
)

router = APIRouter(prefix="/fixed-income", tags=["Fixed Income"])


# ─── Bond Schemas ─────────────────────────────────────────────────────────────

class BondCreate(BaseModel):
    name: str
    bond_type: str  # government, corporate, municipal, treasury, high_yield
    face_value: float
    coupon_rate: float  # e.g. 0.035 = 3.5%
    purchase_price: float
    purchase_date: str  # YYYY-MM-DD
    maturity_date: str  # YYYY-MM-DD
    ticker: Optional[str] = None
    credit_rating: Optional[str] = None
    current_market_value: Optional[float] = None
    currency: str = "USD"
    notes: Optional[str] = None


class BondUpdate(BaseModel):
    name: Optional[str] = None
    bond_type: Optional[str] = None
    face_value: Optional[float] = None
    coupon_rate: Optional[float] = None
    purchase_price: Optional[float] = None
    purchase_date: Optional[str] = None
    maturity_date: Optional[str] = None
    ticker: Optional[str] = None
    credit_rating: Optional[str] = None
    current_market_value: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None


class BondResponse(BaseModel):
    id: str
    name: str
    bond_type: str
    ticker: Optional[str]
    face_value: float
    coupon_rate: float
    purchase_price: float
    current_market_value: Optional[float]
    purchase_date: str
    maturity_date: str
    credit_rating: Optional[str]
    unrealized_pnl: Optional[float]
    currency: str
    notes: Optional[str]


class BondAnalyticsResponse(BaseModel):
    bond_id: str
    name: str
    ytm: float
    current_yield: float
    years_to_maturity: float
    macauley_duration: float
    modified_duration: float
    price_change_100bps: float
    price_change_minus_100bps: float
    annual_coupon: float


class BondSummaryResponse(BaseModel):
    total_bonds: int
    total_face_value: float
    total_market_value: float
    total_unrealized_pnl: float
    by_type: dict


# ─── Term Deposit Schemas ─────────────────────────────────────────────────────

class TermDepositCreate(BaseModel):
    name: str
    bank_name: str
    principal: float
    interest_rate: float  # e.g. 0.018 = 1.8%
    term_months: int
    start_date: str  # YYYY-MM-DD
    maturity_date: str  # YYYY-MM-DD
    compound_frequency: str = "annually"
    auto_renew: bool = False
    notes: Optional[str] = None


class TermDepositUpdate(BaseModel):
    name: Optional[str] = None
    bank_name: Optional[str] = None
    principal: Optional[float] = None
    interest_rate: Optional[float] = None
    term_months: Optional[int] = None
    start_date: Optional[str] = None
    maturity_date: Optional[str] = None
    compound_frequency: Optional[str] = None
    auto_renew: Optional[bool] = None
    notes: Optional[str] = None


class TermDepositResponse(BaseModel):
    id: str
    name: str
    bank_name: str
    principal: float
    interest_rate: float
    term_months: int
    start_date: str
    maturity_date: str
    compound_frequency: str
    accrued_interest: Optional[float]
    maturity_value: Optional[float]
    auto_renew: bool
    notes: Optional[str]


class MaturityAlertResponse(BaseModel):
    id: str
    name: str
    bank_name: str
    principal: float
    maturity_value: float
    maturity_date: str
    days_until_maturity: int
    auto_renew: bool


class TermDepositSummaryResponse(BaseModel):
    total_deposits: int
    total_principal: float
    total_maturity_value: float
    total_accrued_interest: float


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _str_to_date(s: str) -> date:
    return date.fromisoformat(s)


def _bond_to_resp(bond) -> BondResponse:
    return BondResponse(
        id=str(bond.id),
        name=bond.name,
        bond_type=bond.bond_type,
        ticker=bond.ticker,
        face_value=float(bond.face_value),
        coupon_rate=float(bond.coupon_rate),
        purchase_price=float(bond.purchase_price),
        current_market_value=(
            float(bond.current_market_value) if bond.current_market_value else None
        ),
        purchase_date=str(bond.purchase_date),
        maturity_date=str(bond.maturity_date),
        credit_rating=bond.credit_rating,
        unrealized_pnl=float(bond.unrealized_pnl) if bond.unrealized_pnl else None,
        currency=bond.currency,
        notes=bond.notes,
    )


def _td_to_resp(td) -> TermDepositResponse:
    return TermDepositResponse(
        id=str(td.id),
        name=td.name,
        bank_name=td.bank_name,
        principal=float(td.principal),
        interest_rate=float(td.interest_rate),
        term_months=td.term_months,
        start_date=str(td.start_date),
        maturity_date=str(td.maturity_date),
        compound_frequency=td.compound_frequency,
        accrued_interest=float(td.accrued_interest) if td.accrued_interest else None,
        maturity_value=float(td.maturity_value) if td.maturity_value else None,
        auto_renew=td.auto_renew,
        notes=td.notes,
    )


# ─── Bond Routes ─────────────────────────────────────────────────────────────

@router.post("/bonds", response_model=BondResponse)
def create_bond(
    body: BondCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FixedIncomeService(db)
    bond = svc.create_bond(
        user_id=user.id,
        name=body.name,
        bond_type=body.bond_type,
        face_value=body.face_value,
        coupon_rate=body.coupon_rate,
        purchase_price=body.purchase_price,
        purchase_date=_str_to_date(body.purchase_date),
        maturity_date=_str_to_date(body.maturity_date),
        ticker=body.ticker,
        credit_rating=body.credit_rating,
        current_market_value=body.current_market_value,
        currency=body.currency,
        notes=body.notes,
    )
    return _bond_to_resp(bond)


@router.get("/bonds", response_model=list[BondResponse])
def list_bonds(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FixedIncomeService(db)
    return [_bond_to_resp(b) for b in svc.list_bonds(user.id)]


@router.get("/bonds/{bond_id}", response_model=BondResponse)
def get_bond(
    bond_id: UUID,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FixedIncomeService(db)
    bond = svc.get_bond(bond_id, user.id)
    if not bond:
        raise HTTPException(status_code=404, detail="Bond not found")
    return _bond_to_resp(bond)


@router.put("/bonds/{bond_id}", response_model=BondResponse)
def update_bond(
    bond_id: UUID,
    body: BondUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FixedIncomeService(db)
    kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
    if "purchase_date" in kwargs:
        kwargs["purchase_date"] = _str_to_date(kwargs["purchase_date"])
    if "maturity_date" in kwargs:
        kwargs["maturity_date"] = _str_to_date(kwargs["maturity_date"])
    bond = svc.update_bond(bond_id, user.id, **kwargs)
    if not bond:
        raise HTTPException(status_code=404, detail="Bond not found")
    return _bond_to_resp(bond)


@router.delete("/bonds/{bond_id}")
def delete_bond(
    bond_id: UUID,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FixedIncomeService(db)
    if not svc.delete_bond(bond_id, user.id):
        raise HTTPException(status_code=404, detail="Bond not found")
    return {"ok": True}


@router.get("/bonds/{bond_id}/analytics", response_model=BondAnalyticsResponse)
def get_bond_analytics(
    bond_id: UUID,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FixedIncomeService(db)
    analytics = svc.get_bond_analytics(bond_id, user.id)
    if not analytics:
        raise HTTPException(status_code=404, detail="Bond not found")
    return analytics


@router.get("/bonds/summary", response_model=BondSummaryResponse)
def get_bond_summary(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = FixedIncomeService(db)
    return svc.get_bond_summary(user.id)


# ─── Term Deposit Routes ─────────────────────────────────────────────────────

@router.post("/term-deposits", response_model=TermDepositResponse)
def create_term_deposit(
    body: TermDepositCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = TermDepositService(db)
    td = svc.create_term_deposit(
        user_id=user.id,
        name=body.name,
        bank_name=body.bank_name,
        principal=body.principal,
        interest_rate=body.interest_rate,
        term_months=body.term_months,
        start_date=_str_to_date(body.start_date),
        maturity_date=_str_to_date(body.maturity_date),
        compound_frequency=body.compound_frequency,
        auto_renew=body.auto_renew,
        notes=body.notes,
    )
    return _td_to_resp(td)


@router.get("/term-deposits", response_model=list[TermDepositResponse])
def list_term_deposits(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = TermDepositService(db)
    return [_td_to_resp(td) for td in svc.list_term_deposits(user.id)]


@router.get("/term-deposits/{deposit_id}", response_model=TermDepositResponse)
def get_term_deposit(
    deposit_id: UUID,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = TermDepositService(db)
    td = svc.get_term_deposit(deposit_id, user.id)
    if not td:
        raise HTTPException(status_code=404, detail="Term deposit not found")
    return _td_to_resp(td)


@router.put("/term-deposits/{deposit_id}", response_model=TermDepositResponse)
def update_term_deposit(
    deposit_id: UUID,
    body: TermDepositUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = TermDepositService(db)
    kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
    if "start_date" in kwargs:
        kwargs["start_date"] = _str_to_date(kwargs["start_date"])
    if "maturity_date" in kwargs:
        kwargs["maturity_date"] = _str_to_date(kwargs["maturity_date"])
    td = svc.update_term_deposit(deposit_id, user.id, **kwargs)
    if not td:
        raise HTTPException(status_code=404, detail="Term deposit not found")
    return _td_to_resp(td)


@router.delete("/term-deposits/{deposit_id}")
def delete_term_deposit(
    deposit_id: UUID,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = TermDepositService(db)
    if not svc.delete_term_deposit(deposit_id, user.id):
        raise HTTPException(status_code=404, detail="Term deposit not found")
    return {"ok": True}


@router.get(
    "/term-deposits/maturity-alerts",
    response_model=list[MaturityAlertResponse],
)
def get_maturity_alerts(
    days_ahead: int = 90,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = TermDepositService(db)
    return svc.get_maturity_alerts(user.id, days_ahead)


@router.get("/term-deposits/summary", response_model=TermDepositSummaryResponse)
def get_term_deposit_summary(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = TermDepositService(db)
    return svc.get_term_deposit_summary(user.id)

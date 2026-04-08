"""
Fixed Income Service.

Handles:
- Bond CRUD + yield calculations
- Term deposit management
- Bond analytics (duration, interest rate sensitivity)
"""
from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.fixed_income import Bond, BondType, CompoundFrequency, TermDeposit

logger = logging.getLogger(__name__)


# ─── Yield Calculations ──────────────────────────────────────────────────────

def calculate_ytm(
    face_value: float,
    purchase_price: float,
    coupon_rate: float,
    years_to_maturity: float,
    frequency: int = 2,
) -> float:
    """
    Calculate approximate Yield to Maturity (YTM).

    Uses the approximation formula:
    YTM ≈ [C + (F - P) / n] / [(F + P) / 2]

    Where:
    - C = annual coupon payment
    - F = face value
    - P = purchase price
    - n = years to maturity
    """
    annual_coupon = face_value * coupon_rate
    if years_to_maturity <= 0:
        return coupon_rate
    ytm = (annual_coupon + (face_value - purchase_price) / years_to_maturity) / (
        (face_value + purchase_price) / 2
    )
    return max(0.0, ytm)


def calculate_current_yield(
    annual_coupon: float, current_market_value: float
) -> float:
    """Calculate current yield: Annual Coupon / Current Market Price."""
    if current_market_value <= 0:
        return 0.0
    return annual_coupon / current_market_value


def calculate_accrued_interest(
    face_value: float,
    coupon_rate: float,
    purchase_date: date,
    settlement_date: date,
    frequency: int = 2,
) -> float:
    """
    Calculate accrued interest since last coupon payment.
    Uses day-count convention (actual/actual simplified).
    """
    days_in_year = 365.0
    coupon_period_days = days_in_year / frequency
    days_since_last_coupon = (settlement_date - purchase_date).days % int(
        coupon_period_days
    )
    annual_coupon = face_value * coupon_rate
    accrued = annual_coupon * (days_since_last_coupon / days_in_year)
    return round(accrued, 4)


# ─── Duration & Risk Calculations ─────────────────────────────────────────

def calculate_macauley_duration(
    face_value: float,
    coupon_rate: float,
    ytm: float,
    years_to_maturity: float,
    frequency: int = 2,
) -> float:
    """
    Calculate Macauley Duration in years.

    D = Σ [t * PV(CFt)] / P

    Simplified for bonds with semi-annual coupons.
    """
    if years_to_maturity <= 0 or ytm <= -1:
        return 0.0
    r_per_period = ytm / frequency
    n_periods = int(years_to_maturity * frequency)
    coupon_per_period = (face_value * coupon_rate) / frequency

    if r_per_period <= 0:
        return years_to_maturity

    weighted_pv_sum = 0.0
    price = 0.0
    for t in range(1, n_periods + 1):
        if t == n_periods:
            cf = coupon_per_period + face_value / frequency
        else:
            cf = coupon_per_period
        pv = cf / ((1 + r_per_period) ** t)
        weighted_pv_sum += (t / frequency) * pv
        price += pv

    if price <= 0:
        return 0.0
    return weighted_pv_sum / price


def calculate_modified_duration(macauley_duration: float, ytm: float, frequency: int = 2) -> float:
    """Modified Duration = Macauley Duration / (1 + ytm/frequency)."""
    return macauley_duration / (1 + ytm / frequency)


def calculate_price_change(
    modified_duration: float, yield_change_bps: float
) -> float:
    """
    Calculate bond price change given yield change in basis points.
    ΔP ≈ -D * ΔY * P

    yield_change_bps: change in yield in basis points (e.g., 100 = 1%)
    """
    return -modified_duration * (yield_change_bps / 10000.0)


# ─── Term Deposit Calculations ──────────────────────────────────────────────

def calculate_compound_interest(
    principal: float,
    rate: float,
    term_months: int,
    frequency: str = "annually",
) -> float:
    """Calculate maturity value with compound interest."""
    n_per_year = {
        "monthly": 12,
        "quarterly": 4,
        "semi_annually": 2,
        "annually": 1,
    }.get(frequency, 1)

    years = term_months / 12
    n = n_per_year * years
    rate_per_period = rate / n_per_year

    if rate_per_period <= 0:
        return principal
    maturity = principal * ((1 + rate_per_period) ** n)
    return round(maturity, 4)


def calculate_accrued_term_deposit(
    principal: float,
    rate: float,
    start_date: date,
    as_of_date: date,
    frequency: str = "annually",
) -> float:
    """Calculate accrued interest for a term deposit as of a given date."""
    days_elapsed = (as_of_date - start_date).days
    if days_elapsed < 0:
        return 0.0
    days_in_year = 365.0
    # frequency mapping kept for future compound interest support
    _n_per_year = {
        "monthly": 12,
        "quarterly": 4,
        "semi_annually": 2,
        "annually": 1,
    }.get(frequency, 1)
    accrued = principal * rate * (days_elapsed / days_in_year)
    return round(accrued, 4)


# ─── Services ────────────────────────────────────────────────────────────────


class FixedIncomeService:
    """Service for bond operations."""

    def __init__(self, db: Session):
        self.db = db

    # ─── Bond CRUD ────────────────────────────────────────────────────────────

    def create_bond(
        self,
        user_id: UUID,
        name: str,
        bond_type: str,
        face_value: float,
        coupon_rate: float,
        purchase_price: float,
        purchase_date: date,
        maturity_date: date,
        ticker: Optional[str] = None,
        credit_rating: Optional[str] = None,
        current_market_value: Optional[float] = None,
        currency: str = "USD",
        notes: Optional[str] = None,
    ) -> Bond:
        unrealized_pnl = None
        if current_market_value is not None:
            unrealized_pnl = current_market_value - purchase_price

        bond = Bond(
            user_id=user_id,
            name=name,
            bond_type=bond_type,
            ticker=ticker,
            face_value=face_value,
            coupon_rate=coupon_rate,
            purchase_price=purchase_price,
            current_market_value=current_market_value,
            purchase_date=purchase_date,
            maturity_date=maturity_date,
            credit_rating=credit_rating,
            unrealized_pnl=unrealized_pnl,
            currency=currency,
            notes=notes,
        )
        self.db.add(bond)
        self.db.commit()
        self.db.refresh(bond)
        return bond

    def get_bond(self, bond_id: UUID, user_id: UUID) -> Optional[Bond]:
        return (
            self.db.query(Bond)
            .filter(Bond.id == bond_id, Bond.user_id == user_id)
            .first()
        )

    def list_bonds(self, user_id: UUID) -> list[Bond]:
        return self.db.query(Bond).filter(Bond.user_id == user_id).all()

    def update_bond(
        self,
        bond_id: UUID,
        user_id: UUID,
        **kwargs,
    ) -> Optional[Bond]:
        bond = self.get_bond(bond_id, user_id)
        if not bond:
            return None
        for key, value in kwargs.items():
            if hasattr(bond, key) and key not in ("id", "user_id"):
                if key == "unrealized_pnl" and value is None:
                    continue
                setattr(bond, key, value)
        self.db.commit()
        self.db.refresh(bond)
        return bond

    def delete_bond(self, bond_id: UUID, user_id: UUID) -> bool:
        bond = self.get_bond(bond_id, user_id)
        if not bond:
            return False
        self.db.delete(bond)
        self.db.commit()
        return True

    # ─── Analytics ────────────────────────────────────────────────────────────

    def get_bond_analytics(self, bond_id: UUID, user_id: UUID) -> Optional[dict]:
        """Return full analytics for a bond."""
        bond = self.get_bond(bond_id, user_id)
        if not bond:
            return None

        today = date.today()
        years_to_maturity = max(
            0.0, (bond.maturity_date - today).days / 365.0
        )

        ytm = calculate_ytm(
            bond.face_value,
            bond.purchase_price,
            bond.coupon_rate,
            years_to_maturity,
        )
        current_yield = 0.0
        if bond.current_market_value and bond.current_market_value > 0:
            current_yield = calculate_current_yield(
                bond.face_value * bond.coupon_rate,
                bond.current_market_value,
            )

        mac_dur = calculate_macauley_duration(
            bond.face_value,
            bond.coupon_rate,
            ytm,
            years_to_maturity,
        )
        mod_dur = calculate_modified_duration(mac_dur, ytm)

        # Price sensitivity for ±100 bps yield change
        price_change_plus = calculate_price_change(mod_dur, 100)
        price_change_minus = calculate_price_change(mod_dur, -100)

        return {
            "bond_id": str(bond.id),
            "name": bond.name,
            "ytm": round(ytm, 6),
            "current_yield": round(current_yield, 6),
            "years_to_maturity": round(years_to_maturity, 2),
            "macauley_duration": round(mac_dur, 4),
            "modified_duration": round(mod_dur, 4),
            "price_change_100bps": round(price_change_plus, 4),
            "price_change_minus_100bps": round(price_change_minus, 4),
            "annual_coupon": bond.face_value * bond.coupon_rate,
        }

    def get_bond_summary(self, user_id: UUID) -> dict:
        """Aggregate statistics across all bonds."""
        bonds = self.list_bonds(user_id)
        if not bonds:
            return {
                "total_bonds": 0,
                "total_face_value": 0.0,
                "total_market_value": 0.0,
                "total_unrealized_pnl": 0.0,
                "average_ytm": 0.0,
                "by_type": {},
            }

        total_face = sum(float(b.face_value) for b in bonds)
        total_market = sum(
            float(b.current_market_value or b.purchase_price) for b in bonds
        )
        total_pnl = sum(float(b.unrealized_pnl or 0) for b in bonds)

        by_type: dict[str, dict] = {}
        for b in bonds:
            t = b.bond_type
            if t not in by_type:
                by_type[t] = {"count": 0, "face_value": 0.0, "market_value": 0.0}
            by_type[t]["count"] += 1
            by_type[t]["face_value"] += float(b.face_value)
            by_type[t]["market_value"] += float(
                b.current_market_value or b.purchase_price
            )

        return {
            "total_bonds": len(bonds),
            "total_face_value": round(total_face, 4),
            "total_market_value": round(total_market, 4),
            "total_unrealized_pnl": round(total_pnl, 4),
            "by_type": by_type,
        }


class TermDepositService:
    """Service for term deposit operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_term_deposit(
        self,
        user_id: UUID,
        name: str,
        bank_name: str,
        principal: float,
        interest_rate: float,
        term_months: int,
        start_date: date,
        maturity_date: date,
        compound_frequency: str = "annually",
        auto_renew: bool = False,
        notes: Optional[str] = None,
    ) -> TermDeposit:
        maturity_value = calculate_compound_interest(
            principal, interest_rate, term_months, compound_frequency
        )
        accrued = calculate_accrued_term_deposit(
            principal, interest_rate, start_date, date.today(), compound_frequency
        )
        deposit = TermDeposit(
            user_id=user_id,
            name=name,
            bank_name=bank_name,
            principal=principal,
            interest_rate=interest_rate,
            term_months=term_months,
            start_date=start_date,
            maturity_date=maturity_date,
            compound_frequency=compound_frequency,
            accrued_interest=accrued,
            maturity_value=maturity_value,
            auto_renew=auto_renew,
            notes=notes,
        )
        self.db.add(deposit)
        self.db.commit()
        self.db.refresh(deposit)
        return deposit

    def get_term_deposit(self, deposit_id: UUID, user_id: UUID) -> Optional[TermDeposit]:
        return (
            self.db.query(TermDeposit)
            .filter(TermDeposit.id == deposit_id, TermDeposit.user_id == user_id)
            .first()
        )

    def list_term_deposits(self, user_id: UUID) -> list[TermDeposit]:
        return self.db.query(TermDeposit).filter(TermDeposit.user_id == user_id).all()

    def update_term_deposit(
        self, deposit_id: UUID, user_id: UUID, **kwargs
    ) -> Optional[TermDeposit]:
        deposit = self.get_term_deposit(deposit_id, user_id)
        if not deposit:
            return None
        for key, value in kwargs.items():
            if hasattr(deposit, key) and key not in ("id", "user_id"):
                setattr(deposit, key, value)
        self.db.commit()
        self.db.refresh(deposit)
        return deposit

    def delete_term_deposit(self, deposit_id: UUID, user_id: UUID) -> bool:
        deposit = self.get_term_deposit(deposit_id, user_id)
        if not deposit:
            return False
        self.db.delete(deposit)
        self.db.commit()
        return True

    def refresh_accrued(self, deposit: TermDeposit) -> float:
        """Recalculate accrued interest."""
        accrued = calculate_accrued_term_deposit(
            float(deposit.principal),
            float(deposit.interest_rate),
            deposit.start_date,
            date.today(),
            deposit.compound_frequency,
        )
        deposit.accrued_interest = accrued
        self.db.commit()
        return accrued

    def get_maturity_alerts(
        self, user_id: UUID, days_ahead: int = 90
    ) -> list[dict]:
        """Get term deposits maturing within `days_ahead`."""
        deposits = self.list_term_deposits(user_id)
        today = date.today()
        deadline = today + timedelta(days=days_ahead)
        alerts = []
        for d in deposits:
            if today <= d.maturity_date <= deadline:
                days_left = (d.maturity_date - today).days
                alerts.append(
                    {
                        "id": str(d.id),
                        "name": d.name,
                        "bank_name": d.bank_name,
                        "principal": float(d.principal),
                        "maturity_value": float(d.maturity_value or 0),
                        "maturity_date": str(d.maturity_date),
                        "days_until_maturity": days_left,
                        "auto_renew": d.auto_renew,
                    }
                )
        return sorted(alerts, key=lambda x: x["days_until_maturity"])

    def get_term_deposit_summary(self, user_id: UUID) -> dict:
        """Aggregate term deposit statistics."""
        deposits = self.list_term_deposits(user_id)
        if not deposits:
            return {
                "total_deposits": 0,
                "total_principal": 0.0,
                "total_maturity_value": 0.0,
                "total_accrued_interest": 0.0,
            }
        total_principal = sum(float(d.principal) for d in deposits)
        total_maturity = sum(float(d.maturity_value or 0) for d in deposits)
        total_accrued = sum(float(d.accrued_interest or 0) for d in deposits)
        return {
            "total_deposits": len(deposits),
            "total_principal": round(total_principal, 4),
            "total_maturity_value": round(total_maturity, 4),
            "total_accrued_interest": round(total_accrued, 4),
        }

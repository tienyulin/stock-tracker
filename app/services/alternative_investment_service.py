"""
Alternative Investment Service.

Handles CRUD for private equity, REITs, hedge funds, and other
alternative investment tracking.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alternative_investments import (
    AlternativeInvestment,
    LiquidityType,
    PrivateFundNAV,
)
from app.services.yfinance_service import YFinanceService

logger = logging.getLogger(__name__)


class AlternativeInvestmentService:
    """Service for alternative investment operations."""

    def __init__(self, db: Session):
        self.db = db
        self.yfinance = YFinanceService()

    # ─── CRUD ─────────────────────────────────────────────────────────────────

    def create_investment(
        self,
        user_id: UUID,
        name: str,
        investment_type: str,
        ticker: Optional[str] = None,
        liquidity: str = "illiquid",
        cost_basis: float = 0,
        currency: str = "USD",
        purchase_date: Optional[datetime] = None,
        shares_units: Optional[float] = None,
        committed_capital: Optional[float] = None,
        deployed_capital: Optional[float] = None,
        current_nav_per_share: Optional[float] = None,
        current_value: Optional[float] = None,
        current_price: Optional[float] = None,
        rental_income_ytd: Optional[float] = None,
        occupancy_rate: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> AlternativeInvestment:
        """Create a new alternative investment record."""
        investment = AlternativeInvestment(
            user_id=user_id,
            name=name,
            investment_type=investment_type,
            ticker=ticker,
            liquidity=liquidity,
            cost_basis=cost_basis,
            currency=currency,
            purchase_date=purchase_date,
            shares_units=shares_units,
            committed_capital=committed_capital,
            deployed_capital=deployed_capital,
            current_nav_per_share=current_nav_per_share,
            current_value=current_value,
            current_price=current_price,
            rental_income_ytd=rental_income_ytd,
            occupancy_rate=occupancy_rate,
            notes=notes,
        )
        self.db.add(investment)
        self.db.commit()
        self.db.refresh(investment)
        return investment

    def get_investment(self, investment_id: UUID, user_id: UUID) -> Optional[AlternativeInvestment]:
        """Get a single alternative investment by ID."""
        return (
            self.db.query(AlternativeInvestment)
            .filter(
                AlternativeInvestment.id == investment_id,
                AlternativeInvestment.user_id == user_id,
            )
            .first()
        )

    def get_investments(
        self,
        user_id: UUID,
        investment_type: Optional[str] = None,
        liquidity: Optional[str] = None,
        active_only: bool = True,
    ) -> list[AlternativeInvestment]:
        """List all alternative investments for a user."""
        q = self.db.query(AlternativeInvestment).filter(
            AlternativeInvestment.user_id == user_id
        )
        if active_only:
            q = q.filter(AlternativeInvestment.is_active)
        if investment_type:
            q = q.filter(AlternativeInvestment.investment_type == investment_type)
        if liquidity:
            q = q.filter(AlternativeInvestment.liquidity == liquidity)
        return q.order_by(AlternativeInvestment.created_at.desc()).all()

    def update_investment(
        self,
        investment_id: UUID,
        user_id: UUID,
        **kwargs,
    ) -> Optional[AlternativeInvestment]:
        """Update an alternative investment."""
        investment = self.get_investment(investment_id, user_id)
        if not investment:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(investment, key):
                setattr(investment, key, value)
        self.db.commit()
        self.db.refresh(investment)
        return investment

    def delete_investment(self, investment_id: UUID, user_id: UUID) -> bool:
        """Soft-delete (deactivate) an alternative investment."""
        investment = self.get_investment(investment_id, user_id)
        if not investment:
            return False
        investment.is_active = False
        self.db.commit()
        return True

    # ─── NAV Management ───────────────────────────────────────────────────────

    def add_nav_record(
        self,
        investment_id: UUID,
        user_id: UUID,
        nav_date: datetime,
        nav_per_share: float,
        total_value: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> Optional[PrivateFundNAV]:
        """Add a NAV record for a private fund."""
        investment = self.get_investment(investment_id, user_id)
        if not investment:
            return None
        unrealized = None
        if total_value and investment.cost_basis:
            unrealized = total_value - investment.cost_basis

        nav = PrivateFundNAV(
            investment_id=investment_id,
            nav_date=nav_date,
            nav_per_share=nav_per_share,
            total_value=total_value,
            unrealized_gain_loss=unrealized,
            notes=notes,
        )
        self.db.add(nav)
        # Update current NAV on the investment
        investment.current_nav_per_share = nav_per_share
        if total_value:
            investment.current_value = total_value
        self.db.commit()
        self.db.refresh(nav)
        return nav

    def get_nav_history(
        self,
        investment_id: UUID,
        user_id: UUID,
    ) -> list[PrivateFundNAV]:
        """Get NAV history for a fund."""
        investment = self.get_investment(investment_id, user_id)
        if not investment:
            return []
        return (
            self.db.query(PrivateFundNAV)
            .filter(PrivateFundNAV.investment_id == investment_id)
            .order_by(PrivateFundNAV.nav_date.desc())
            .all()
        )

    # ─── Summary & Analytics ─────────────────────────────────────────────────

    def get_summary(self, user_id: UUID) -> dict:
        """Get alternative investments summary dashboard."""
        investments = self.get_investments(user_id, active_only=True)
        if not investments:
            return {
                "total_value": 0,
                "total_cost_basis": 0,
                "total_unrealized_gain": 0,
                "unrealized_gain_percent": 0,
                "by_type": {},
                "liquidity_analysis": {
                    "liquid_value": 0,
                    "liquid_percent": 0,
                    "semi_liquid_value": 0,
                    "semi_liquid_percent": 0,
                    "illiquid_value": 0,
                    "illiquid_percent": 0,
                    "total_value": 0,
                    "currency": "USD",
                },
                "currency": "USD",
            }

        total_value = sum(
            inv.current_value or inv.cost_basis or 0 for inv in investments
        )
        total_cost = sum(inv.cost_basis or 0 for inv in investments)
        unrealized = total_value - total_cost
        unrealized_pct = (unrealized / total_cost * 100) if total_cost > 0 else 0

        # By type
        by_type: dict[str, dict[str, float]] = {}
        for inv in investments:
            t = inv.investment_type
            if t not in by_type:
                by_type[t] = {"value": 0, "cost": 0, "count": 0}
            by_type[t]["value"] += inv.current_value or inv.cost_basis or 0
            by_type[t]["cost"] += inv.cost_basis or 0
            by_type[t]["count"] += 1

        # Liquidity analysis
        liquid = sum(
            inv.current_value or inv.cost_basis or 0
            for inv in investments
            if inv.liquidity == LiquidityType.LIQUID.value
        )
        semi = sum(
            inv.current_value or inv.cost_basis or 0
            for inv in investments
            if inv.liquidity == LiquidityType.SEMI_LIQUID.value
        )
        illiquid = sum(
            inv.current_value or inv.cost_basis or 0
            for inv in investments
            if inv.liquidity == LiquidityType.ILLIQUID.value
        )

        return {
            "total_value": round(total_value, 2),
            "total_cost_basis": round(total_cost, 2),
            "total_unrealized_gain": round(unrealized, 2),
            "unrealized_gain_percent": round(unrealized_pct, 2),
            "by_type": {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in by_type.items()},
            "liquidity_analysis": {
                "liquid_value": round(liquid, 2),
                "liquid_percent": round(liquid / total_value * 100, 2) if total_value > 0 else 0,
                "semi_liquid_value": round(semi, 2),
                "semi_liquid_percent": round(semi / total_value * 100, 2) if total_value > 0 else 0,
                "illiquid_value": round(illiquid, 2),
                "illiquid_percent": round(illiquid / total_value * 100, 2) if total_value > 0 else 0,
                "total_value": round(total_value, 2),
                "currency": "USD",
            },
            "currency": "USD",
        }

    def get_reits_quote(self, ticker: str) -> Optional[dict]:
        """Get REIT quote from yfinance."""
        try:
            return self.yfinance.get_quote(ticker)
        except Exception as e:
            logger.warning(f"Failed to get REIT quote for {ticker}: {e}")
            return None

    def calculate_rental_yield(
        self,
        annual_rental_income: float,
        property_value: float,
    ) -> float:
        """Calculate rental yield percentage."""
        if property_value <= 0:
            return 0
        return round(annual_rental_income / property_value * 100, 2)

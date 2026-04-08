"""
Cash Flow Forecasting & Liquidity Planning Service.

Provides:
- CashFlowService: CRUD + monthly aggregation
- CashFlowForecastService: 3/6/12 month forecasting
- LiquidityPlanningService: liquidity tier analysis
- EmergencyFundService: emergency fund tracking & gap calculation
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.cash_flow_db import (
    CashFlowEntryModel,
    CashFlowEntryType,
    EmergencyFundModel,
    LargeExpenseModel,
    LiquidityAssetModel,
)


class CashFlowService:
    """Service for cash flow entry management and monthly aggregation."""

    def __init__(self, db: Session):
        self.db = db

    def create_entry(
        self,
        user_id: uuid.UUID,
        entry_type: str,
        category: str,
        amount: float,
        entry_date: date,
        description: Optional[str] = None,
        is_recurring: bool = False,
        recurring_frequency: Optional[str] = None,
        source: Optional[str] = None,
    ) -> CashFlowEntryModel:
        entry = CashFlowEntryModel(
            user_id=user_id,
            entry_type=entry_type,
            category=category,
            amount=Decimal(str(amount)),
            date=entry_date,
            description=description,
            is_recurring=is_recurring,
            recurring_frequency=recurring_frequency,
            source=source,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_entries(
        self,
        user_id: uuid.UUID,
        year_month: Optional[str] = None,
        entry_type: Optional[str] = None,
    ) -> list[CashFlowEntryModel]:
        q = select(CashFlowEntryModel).where(CashFlowEntryModel.user_id == user_id)
        if year_month:
            q = q.where(
                func.to_char(CashFlowEntryModel.date, "YYYY-MM") == year_month
            )
        if entry_type:
            q = q.where(CashFlowEntryModel.entry_type == entry_type)
        q = q.order_by(CashFlowEntryModel.date.desc())
        result = self.db.execute(q)
        return list(result.scalars().all())

    def delete_entry(self, entry_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        entry = self.db.execute(
            select(CashFlowEntryModel).where(
                CashFlowEntryModel.id == entry_id,
                CashFlowEntryModel.user_id == user_id,
            )
        ).scalar_one_or_none()
        if not entry:
            return False
        self.db.delete(entry)
        self.db.commit()
        return True

    def get_monthly_cashflow(self, user_id: uuid.UUID, year_month: str) -> dict:
        """Calculate cash flow summary for a specific month."""
        entries = self.get_entries(user_id, year_month=year_month)

        income = Decimal("0")
        expense = Decimal("0")
        passive = Decimal("0")
        active = Decimal("0")
        income_by_cat: dict[str, Decimal] = {}
        expense_by_cat: dict[str, Decimal] = {}

        passive_cats = {"dividend", "interest", "rental", "other_passive"}

        for e in entries:
            amt = e.amount
            cat = e.category
            if e.entry_type == "income":
                income += amt
                income_by_cat[cat] = income_by_cat.get(cat, Decimal("0")) + amt
                if cat in passive_cats:
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


class CashFlowForecastService:
    """Service for cash flow forecasting."""

    def __init__(self, db: Session):
        self.db = db
        self.cashflow = CashFlowService(db)

    def get_forecast(
        self,
        user_id: uuid.UUID,
        months: int = 3,
    ) -> dict:
        """Generate cash flow forecast for the next N months."""
        if months not in (3, 6, 12):
            raise ValueError("months must be 3, 6, or 12")

        now = datetime.utcnow()
        monthly_flows = []
        for i in range(1, 4):
            ym = (now - timedelta(days=30 * i)).strftime("%Y-%m")
            flow = self.cashflow.get_monthly_cashflow(user_id, ym)
            if flow["total_income"] > 0 or flow["total_expense"] > 0:
                monthly_flows.append(flow)

        if not monthly_flows:
            return {
                "forecast_months": months,
                "forecasted_balance": 0.0,
                "shortfall_months": [],
                "confidence_score": 0.3,
            }

        avg_income = sum(f["total_income"] for f in monthly_flows) / len(monthly_flows)
        avg_expense = sum(f["total_expense"] for f in monthly_flows) / len(monthly_flows)
        avg_net = avg_income - avg_expense

        forecasted_balance = avg_net * months
        shortfall_months = [
            f"Month {i+1}" for i in range(months) if avg_expense > avg_income
        ]

        # Confidence based on variance
        if len(monthly_flows) >= 2:
            net_values = [f["net_cash_flow"] for f in monthly_flows]
            variance = sum((v - avg_net) ** 2 for v in net_values) / len(net_values)
            std_dev = variance ** 0.5
            confidence = max(0.3, min(0.9, 1.0 - (std_dev / (abs(avg_net) + 1) * 0.1)))
        else:
            confidence = 0.5

        return {
            "forecast_months": months,
            "forecasted_balance": float(forecasted_balance),
            "shortfall_months": shortfall_months,
            "confidence_score": confidence,
        }


class LiquidityPlanningService:
    """Service for liquidity position analysis."""

    def __init__(self, db: Session):
        self.db = db
        self.cashflow = CashFlowService(db)

    def get_position(
        self,
        user_id: uuid.UUID,
        high_liquidity: float = 0,
        medium_liquidity: float = 0,
        low_liquidity: float = 0,
    ) -> dict:
        """Get liquidity position and coverage analysis."""
        now = datetime.utcnow()
        total_expense = Decimal("0")
        count = 0
        for i in range(1, 4):
            ym = (now - timedelta(days=30 * i)).strftime("%Y-%m")
            flow = self.cashflow.get_monthly_cashflow(user_id, ym)
            if flow["total_expense"] > 0:
                total_expense += Decimal(str(flow["total_expense"]))
                count += 1

        avg_monthly_expense = float(total_expense / count) if count > 0 else 1.0

        total_liquid = high_liquidity + medium_liquidity + low_liquidity
        months_covered = total_liquid / avg_monthly_expense if avg_monthly_expense > 0 else 0.0
        liquidity_ratio = high_liquidity / avg_monthly_expense if avg_monthly_expense > 0 else 0.0

        return {
            "total_liquid_assets": total_liquid,
            "months_of_expenses_covered": float(months_covered),
            "liquidity_ratio": float(liquidity_ratio),
            "high_liquidity": high_liquidity,
            "medium_liquidity": medium_liquidity,
            "low_liquidity": low_liquidity,
        }


class EmergencyFundService:
    """Service for emergency fund tracking."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_fund(
        self,
        user_id: uuid.UUID,
        current_amount: float,
        monthly_expenses_estimate: float,
    ) -> EmergencyFundModel:
        fund = self.db.execute(
            select(EmergencyFundModel).where(EmergencyFundModel.user_id == user_id)
        ).scalar_one_or_none()

        if fund:
            fund.current_amount = Decimal(str(current_amount))
            fund.monthly_expenses_estimate = Decimal(str(monthly_expenses_estimate))
            self.db.commit()
            self.db.refresh(fund)
        else:
            fund = EmergencyFundModel(
                user_id=user_id,
                current_amount=Decimal(str(current_amount)),
                monthly_expenses_estimate=Decimal(str(monthly_expenses_estimate)),
            )
            self.db.add(fund)
            self.db.commit()
            self.db.refresh(fund)
        return fund

    def get_status(self, user_id: uuid.UUID) -> dict:
        """Get emergency fund status."""
        fund = self.db.execute(
            select(EmergencyFundModel).where(EmergencyFundModel.user_id == user_id)
        ).scalar_one_or_none()

        if not fund:
            return {
                "current_fund": 0.0,
                "recommended_minimum": 0.0,
                "recommended_ideal": 0.0,
                "coverage_months": 0.0,
                "shortfall": 0.0,
                "progress_percentage": 0.0,
                "is_adequate": False,
            }

        current = float(fund.current_amount)
        monthly_exp = float(fund.monthly_expenses_estimate)
        recommended_min = monthly_exp * 3
        recommended_ideal = monthly_exp * 6

        coverage = current / monthly_exp if monthly_exp > 0 else 0.0
        shortfall = max(0.0, recommended_ideal - current)
        progress = min((current / recommended_ideal * 100), 100) if recommended_ideal > 0 else 0.0

        return {
            "current_fund": current,
            "recommended_minimum": recommended_min,
            "recommended_ideal": recommended_ideal,
            "coverage_months": float(coverage),
            "shortfall": shortfall,
            "progress_percentage": float(progress),
            "is_adequate": coverage >= 3,
        }


class LargeExpenseService:
    """Service for planned large expenses."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: uuid.UUID,
        description: str,
        estimated_amount: float,
        planned_date: date,
    ) -> LargeExpenseModel:
        months_until = max(0, (planned_date - datetime.utcnow().date()).days // 30)
        monthly_savings_needed = (
            Decimal(str(estimated_amount)) / months_until
            if months_until > 0
            else Decimal(str(estimated_amount))
        )
        expense = LargeExpenseModel(
            user_id=user_id,
            description=description,
            estimated_amount=Decimal(str(estimated_amount)),
            planned_date=planned_date,
            monthly_savings_needed=monthly_savings_needed,
        )
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def list_expenses(self, user_id: uuid.UUID) -> list[LargeExpenseModel]:
        result = self.db.execute(
            select(LargeExpenseModel)
            .where(LargeExpenseModel.user_id == user_id)
            .order_by(LargeExpenseModel.planned_date.asc())
        )
        return list(result.scalars().all())

    def update_status(
        self, expense_id: uuid.UUID, user_id: uuid.UUID, status: str
    ) -> Optional[LargeExpenseModel]:
        expense = self.db.execute(
            select(LargeExpenseModel).where(
                LargeExpenseModel.id == expense_id,
                LargeExpenseModel.user_id == user_id,
            )
        ).scalar_one_or_none()
        if not expense:
            return None
        expense.status = status
        self.db.commit()
        self.db.refresh(expense)
        return expense

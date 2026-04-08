"""
Passive Income Service — business logic for passive income tracking.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.passive_income import (
    FireGoal,
    PassiveIncomeRecord,
    PassiveIncomeSource,
)


class PassiveIncomeService:
    """Service for managing passive income sources and records."""

    def __init__(self, db: Session):
        self.db = db

    # ─── Sources ──────────────────────────────────────────────────────────────

    def create_source(
        self,
        user_id: uuid.UUID,
        name: str,
        source_type: str,
        expected_monthly_income: float = 0,
        expected_annual_income: float = 0,
        currency: str = "USD",
        description: Optional[str] = None,
        yield_on_cost: Optional[float] = None,
        start_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> PassiveIncomeSource:
        source = PassiveIncomeSource(
            user_id=user_id,
            name=name,
            source_type=source_type,
            description=description,
            currency=currency,
            expected_monthly_income=expected_monthly_income,
            expected_annual_income=expected_annual_income,
            yield_on_cost=yield_on_cost,
            start_date=start_date,
            notes=notes,
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def get_sources(self, user_id: uuid.UUID, active_only: bool = True) -> list[PassiveIncomeSource]:
        query = select(PassiveIncomeSource).where(PassiveIncomeSource.user_id == user_id)
        if active_only:
            query = query.where(PassiveIncomeSource.is_active == True)  # noqa: E712
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_source(self, user_id: uuid.UUID, source_id: uuid.UUID) -> Optional[PassiveIncomeSource]:
        result = self.db.execute(
            select(PassiveIncomeSource).where(
                PassiveIncomeSource.id == source_id,
                PassiveIncomeSource.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    def update_source(
        self,
        source_id: uuid.UUID,
        user_id: uuid.UUID,
        **kwargs,
    ) -> Optional[PassiveIncomeSource]:
        source = self.get_source(user_id, source_id)
        if not source:
            return None
        for key, value in kwargs.items():
            if hasattr(source, key) and key not in ("id", "user_id", "created_at"):
                setattr(source, key, value)
        self.db.commit()
        self.db.refresh(source)
        return source

    def delete_source(self, user_id: uuid.UUID, source_id: uuid.UUID) -> bool:
        source = self.get_source(user_id, source_id)
        if not source:
            return False
        self.db.delete(source)
        self.db.commit()
        return True

    # ─── Records ───────────────────────────────────────────────────────────────

    def add_record(
        self,
        user_id: uuid.UUID,
        source_id: uuid.UUID,
        amount: float,
        record_date: datetime,
        currency: str = "USD",
        record_type: str = "received",
        notes: Optional[str] = None,
    ) -> PassiveIncomeRecord:
        record = PassiveIncomeRecord(
            user_id=user_id,
            source_id=source_id,
            amount=amount,
            currency=currency,
            record_date=record_date,
            record_type=record_type,
            notes=notes,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_records(
        self,
        user_id: uuid.UUID,
        source_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[PassiveIncomeRecord]:
        query = select(PassiveIncomeRecord).where(PassiveIncomeRecord.user_id == user_id)
        if source_id:
            query = query.where(PassiveIncomeRecord.source_id == source_id)
        if start_date:
            query = query.where(PassiveIncomeRecord.record_date >= start_date)
        if end_date:
            query = query.where(PassiveIncomeRecord.record_date <= end_date)
        query = query.order_by(PassiveIncomeRecord.record_date.desc())
        result = self.db.execute(query)
        return list(result.scalars().all())

    # ─── Aggregations ──────────────────────────────────────────────────────────

    def get_monthly_summary(
        self, user_id: uuid.UUID, year: int, month: int
    ) -> dict:
        """Return total passive income for a given year-month, broken by source type."""
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)

        records = self.get_records(user_id, start_date=start, end_date=end)
        total = sum(r.amount for r in records if r.record_type == "received")
        by_type: dict[str, float] = {}
        for r in records:
            if r.record_type == "received":
                by_type[r.source.source_type if r.source else "unknown"] = (
                    by_type.get(r.source.source_type if r.source else "unknown", 0) + r.amount
                )
        return {"total": total, "by_type": by_type, "currency": "USD"}

    def get_annual_summary(self, user_id: uuid.UUID, year: int) -> dict:
        """Return 12-month passive income summary for a given year."""
        start = datetime(year, 1, 1)
        end = datetime(year + 1, 1, 1)
        records = self.get_records(user_id, start_date=start, end_date=end)

        months = {m: 0.0 for m in range(1, 13)}
        for r in records:
            if r.record_type == "received":
                m = r.record_date.month
                months[m] = months.get(m, 0) + r.amount

        total = sum(months.values())
        return {
            "year": year,
            "monthly": [months[m] for m in range(1, 13)],
            "total": total,
            "currency": "USD",
        }

    def get_yield_on_cost(self, source: PassiveIncomeSource) -> Optional[float]:
        """Calculate yield on cost if cost basis is available."""
        if not source.expected_annual_income:
            return None
        # For rental / interest, yield_on_cost stored directly
        return source.yield_on_cost

    # ─── FIRE Goals ─────────────────────────────────────────────────────────────

    def get_fire_goal(self, user_id: uuid.UUID) -> Optional[FireGoal]:
        result = self.db.execute(
            select(FireGoal).where(
                FireGoal.user_id == user_id,
                FireGoal.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    def upsert_fire_goal(
        self,
        user_id: uuid.UUID,
        target_annual_income: float,
        monthly_expenses: float,
        target_date: Optional[datetime] = None,
        currency: str = "USD",
    ) -> FireGoal:
        existing = self.get_fire_goal(user_id)
        current_passive = self._get_current_annual_passive(user_id)
        progress = (
            (current_passive / target_annual_income * 100)
            if target_annual_income > 0
            else 0
        )
        if existing:
            existing.target_annual_income = target_annual_income
            existing.monthly_expenses = monthly_expenses
            existing.target_date = target_date
            existing.currency = currency
            existing.current_passive_income = current_passive
            existing.progress_percentage = min(progress, 100)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        goal = FireGoal(
            user_id=user_id,
            target_annual_income=target_annual_income,
            monthly_expenses=monthly_expenses,
            target_date=target_date,
            currency=currency,
            current_passive_income=current_passive,
            progress_percentage=min(progress, 100),
        )
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def _get_current_annual_passive(self, user_id: uuid.UUID) -> float:
        """Sum last 12 months of recorded passive income."""
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        records = self.get_records(user_id, start_date=twelve_months_ago)
        return sum(r.amount for r in records if r.record_type == "received")

    def get_fire_progress(self, user_id: uuid.UUID) -> Optional[dict]:
        """Return FIRE progress dashboard data."""
        goal = self.get_fire_goal(user_id)
        if not goal:
            return None
        return {
            "target_annual_income": goal.target_annual_income,
            "current_passive_income": goal.current_passive_income,
            "progress_percentage": goal.progress_percentage,
            "monthly_expenses": goal.monthly_expenses,
            "monthly_target": goal.target_annual_income / 12,
            "months_to_target": self._months_to_fire(goal),
            "target_date": goal.target_date,
            "currency": goal.currency,
        }

    def _months_to_fire(self, goal: FireGoal) -> int:
        if goal.progress_percentage >= 100:
            return 0
        if goal.progress_percentage <= 0:
            return -1  # impossible
        monthly_gap = (goal.target_annual_income / 12) - goal.current_passive_income
        if monthly_gap <= 0:
            return 0
        # rough estimate: assume 7% annual growth in passive income
        months = 0
        current = goal.current_passive_income
        monthly_rate = 0.07 / 12
        while current < goal.target_annual_income and months < 1200:
            current = current * (1 + monthly_rate)
            months += 1
        return months if months < 1200 else -1

"""
SQLAlchemy models for Cash Flow Forecasting & Liquidity Planning.
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CashFlowEntryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class CashFlowEntryModel(Base):
    """Individual cash flow entry (income or expense)."""

    __tablename__ = "cash_flow_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    entry_type: Mapped[str] = mapped_column(String(10), nullable=False)  # income | expense
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_recurring: Mapped[bool] = mapped_column(default=False)
    recurring_frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # monthly | quarterly | annual
    source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EmergencyFundModel(Base):
    """Emergency fund record for a user."""

    __tablename__ = "emergency_funds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    current_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    monthly_expenses_estimate: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LiquidityAssetModel(Base):
    """Asset classified by liquidity tier."""

    __tablename__ = "liquidity_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    liquidity_level: Mapped[str] = mapped_column(String(20), nullable=False)  # high | medium | low | illiquid
    current_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LargeExpenseModel(Base):
    """Planned large expense."""

    __tablename__ = "large_expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    estimated_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    planned_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="planned")  # planned | in_progress | completed | cancelled
    monthly_savings_needed: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

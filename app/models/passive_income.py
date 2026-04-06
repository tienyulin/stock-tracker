"""
SQLAlchemy models for Passive Income tracking.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.models import User


class PassiveIncomeSource(Base):
    """User's passive income source (rental, interest, royalty, pension, etc.)."""

    __tablename__ = "passive_income_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'dividend', 'rental', 'interest', 'royalty', 'pension', 'social_security', 'p2p', 'other'
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    expected_monthly_income: Mapped[float] = mapped_column(Float, default=0)
    expected_annual_income: Mapped[float] = mapped_column(Float, default=0)
    yield_on_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # % if applicable
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="passive_income_sources")
    records: Mapped[list["PassiveIncomeRecord"]] = relationship(
        "PassiveIncomeRecord", back_populates="source", cascade="all, delete-orphan"
    )

    class Config:
        from_attributes = True


class PassiveIncomeRecord(Base):
    """Individual passive income payment record."""

    __tablename__ = "passive_income_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("passive_income_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    record_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    record_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="received"
    )  # 'received', 'expected', 'missed'
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    source: Mapped["PassiveIncomeSource"] = relationship(
        "PassiveIncomeSource", back_populates="records"
    )

    class Config:
        from_attributes = True


class FireGoal(Base):
    """FIRE (Financial Independence, Retire Early) goal tracking."""

    __tablename__ = "fire_goals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_annual_income: Mapped[float] = mapped_column(Float, nullable=False)
    target_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    monthly_expenses: Mapped[float] = mapped_column(Float, nullable=False)
    current_passive_income: Mapped[float] = mapped_column(Float, default=0)
    progress_percentage: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="fire_goals")

    class Config:
        from_attributes = True


# Add relationships to User model
User.passive_income_sources: Mapped[list["PassiveIncomeSource"]] = relationship(
    "PassiveIncomeSource", back_populates="user", cascade="all, delete-orphan"
)
User.fire_goals: Mapped[list["FireGoal"]] = relationship(
    "FireGoal", back_populates="user", cascade="all, delete-orphan"
)

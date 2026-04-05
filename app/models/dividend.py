"""
SQLAlchemy models for Dividend tracking.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.models import User


class DividendPayment(Base):
    """Record of a dividend payment for a user's holding."""

    __tablename__ = "dividend_payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    ex_dividend_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount_per_share: Mapped[float] = mapped_column(Float, nullable=False)
    shares_owned: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    class Config:
        from_attributes = True


class DividendHolding(Base):
    """Tracks dividend information for a holding position."""

    __tablename__ = "dividend_holdings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    shares_owned: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    cost_basis: Mapped[float] = mapped_column(Float, nullable=False, default=0)  # Total cost
    annual_dividend: Mapped[float] = mapped_column(Float, nullable=False, default=0)  # Annual dividend per share
    dividend_yield: Mapped[float] = mapped_column(Float, nullable=False, default=0)  # Current yield %
    yield_on_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)  # YOC %
    last_dividend_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dividend_growth_rate: Mapped[float] = mapped_column(Float, default=0)  # YoY growth %
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    class Config:
        from_attributes = True


class ExDividendCalendar(Base):
    """Upcoming ex-dividend and payment dates calendar."""

    __tablename__ = "ex_dividend_calendar"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    ex_dividend_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount_per_share: Mapped[float] = mapped_column(Float, nullable=False)
    is_upcoming: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    class Config:
        from_attributes = True

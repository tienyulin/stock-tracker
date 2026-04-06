"""
Fixed Income Models: Bond and Term Deposit.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BondType(str, Enum):
    GOVERNMENT = "government"
    CORPORATE = "corporate"
    MUNICIPAL = "municipal"
    TREASURY = "treasury"
    HIGH_YIELD = "high_yield"


class CompoundFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUALLY = "semi_annually"
    ANNUALLY = "annually"


class Bond(Base):
    __tablename__ = "bonds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    bond_type: Mapped[str] = mapped_column(String(50), nullable=False)  # BondType
    ticker: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Terms
    face_value: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    coupon_rate: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)  # e.g. 0.035 = 3.5%
    purchase_price: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    current_market_value: Mapped[Optional[float]] = mapped_column(
        Numeric(16, 4), nullable=True
    )

    # Dates
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Risk
    credit_rating: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # P&L
    unrealized_pnl: Mapped[Optional[float]] = mapped_column(
        Numeric(16, 4), nullable=True
    )

    currency: Mapped[str] = mapped_column(String(3), default="USD")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="bonds")


class TermDeposit(Base):
    __tablename__ = "term_deposits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Terms
    principal: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    interest_rate: Mapped[float] = mapped_column(
        Numeric(8, 6), nullable=False
    )  # e.g. 0.018 = 1.8%
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)

    # Dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Compound
    compound_frequency: Mapped[str] = mapped_column(
        String(20), default="annually"
    )  # CompoundFrequency

    # Calculated
    accrued_interest: Mapped[Optional[float]] = mapped_column(
        Numeric(16, 4), nullable=True
    )
    maturity_value: Mapped[Optional[float]] = mapped_column(
        Numeric(16, 4), nullable=True
    )

    # Options
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="term_deposits")

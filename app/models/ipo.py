"""
SQLAlchemy models for IPO tracking.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.models import User


class IPOStatus(str, Enum):
    UPCOMING = "upcoming"
    FILING = "filing"
    ALLOCATED = "allocated"
    LISTED = "listed"
    WITHDRAWN = "withdrawn"


class IPOAlertType(str, Enum):
    DEADLINE = "deadline"
    ALLOCATION = "allocation"
    PERFORMANCE = "performance"


class IPORecord(Base):
    """IPO tracking record."""

    __tablename__ = "ipo_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ticker: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    exchange: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Pricing
    ipo_price_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ipo_price_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_ipo_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Shares
    shares_offered: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    oversubscription_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Dates
    application_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    listing_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    first_trading_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Details
    underwriter: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=IPOStatus.UPCOMING.value
    )
    estimated_market_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raising_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    alerts: Mapped[list["IPOAlert"]] = relationship(
        "IPOAlert", back_populates="ipo_record", cascade="all, delete-orphan"
    )

    class Config:
        from_attributes = True


class IPOAlert(Base):
    """IPO alert record."""

    __tablename__ = "ipo_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    ipo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ipo_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    alert_type: Mapped[str] = mapped_column(
        String(20), default=IPOAlertType.DEADLINE.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    ipo_record: Mapped["IPORecord"] = relationship("IPORecord", back_populates="alerts")

    class Config:
        from_attributes = True


# Add relationships back to User model
User.ipo_records = relationship(
    "IPORecord", back_populates="user", cascade="all, delete-orphan"
)
User.ipo_alerts = relationship(
    "IPOAlert", back_populates="user", cascade="all, delete-orphan"
)

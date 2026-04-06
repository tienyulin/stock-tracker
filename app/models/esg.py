"""
ESG & Sustainable Investing Models.
"""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
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


class ControversyType(str, Enum):
    HUMAN_RIGHTS = "human_rights"
    WEAPONS = "weapons"
    TOBACCO = "tobacco"
    GAMBLING = "gambling"
    SUPPLY_CHAIN = "supply_chain"
    ENVIRONMENTAL = "environmental"
    GOVERNANCE = "governance"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"


class ExclusionListType(str, Enum):
    NEGATIVE_SCREENING = "negative_screening"
    ETHICAL_EXCLUSION = "ethical_exclusion"


class EsgScore(Base):
    """ESG score for a company/ticker."""

    __tablename__ = "esg_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Identity
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # ESG Scores (0-100)
    esg_total_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    environmental_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    social_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    governance_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    # Environmental metrics
    carbon_footprint_tons: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    water_usage_m3: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    waste_tons: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)

    # Data source
    data_source: Mapped[str] = mapped_column(String(50), default="msci")  # msci, sustainalytics, tructost

    # Timestamps
    rating_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="esg_scores")


class ControversyAlert(Base):
    """Controversy/alert for a company."""

    __tablename__ = "controversy_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)

    controversy_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")

    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    alert_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, dismissed, resolved

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="controversy_alerts")


class ExclusionList(Base):
    """User's negative screening / exclusion list."""

    __tablename__ = "exclusion_lists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    list_type: Mapped[str] = mapped_column(String(50), nullable=False)  # negative_screening, ethical_exclusion
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ticker: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="exclusion_lists")


class EsgTrend(Base):
    """Monthly ESG score trend history."""

    __tablename__ = "esg_trends"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    month: Mapped[date] = mapped_column(Date, nullable=False)

    esg_total_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    environmental_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    social_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    governance_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="esg_trends")

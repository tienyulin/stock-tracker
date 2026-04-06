"""
SQLAlchemy models for Alternative Investments tracking.
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


class LiquidityType(str, Enum):
    """Liquidity classification for alternative investments."""
    LIQUID = "liquid"           # Listed, publicly tradable
    SEMI_LIQUID = "semi_liquid" # ETFs, closed-end funds with secondary markets
    ILLIQUID = "illiquid"       # Private equity, private credit, direct real estate


class AlternativeInvestmentType(str, Enum):
    """Types of alternative investments."""
    PRIVATE_EQUITY = "private_equity"
    VENTURE_CAPITAL = "venture_capital"
    PRIVATE_CREDIT = "private_credit"
    HEDGE_FUND = "hedge_fund"
    REIT_LISTED = "reit_listed"
    REIT_NONLISTED = "reit_nonlisted"
    COMMODITY = "commodity"
    PRECIOUS_METALS = "precious_metals"
    OTHER = "other"


class AlternativeInvestment(Base):
    """User's alternative investment holding."""

    __tablename__ = "alternative_investments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    investment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ticker: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    liquidity: Mapped[str] = mapped_column(String(20), default=LiquidityType.ILLIQUID.value)
    
    # Cost basis
    cost_basis: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    purchase_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    shares_units: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Private fund specific
    committed_capital: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deployed_capital: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_nav_per_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # REITs specific
    rental_income_ytd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    occupancy_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Current value (updated manually or via NAV)
    current_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="alternative_investments")
    nav_history: Mapped[list["PrivateFundNAV"]] = relationship(
        "PrivateFundNAV", back_populates="investment", cascade="all, delete-orphan"
    )

    class Config:
        from_attributes = True


class PrivateFundNAV(Base):
    """NAV history for private funds (PE/VC/Hedge Funds)."""

    __tablename__ = "private_fund_nav"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    investment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alternative_investments.id", ondelete="CASCADE"),
        nullable=False,
    )
    nav_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    nav_per_share: Mapped[float] = mapped_column(Float, nullable=False)
    total_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unrealized_gain_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    investment: Mapped["AlternativeInvestment"] = relationship(
        "AlternativeInvestment", back_populates="nav_history"
    )

    class Config:
        from_attributes = True


# Add relationship back to User model
User.alternative_investments = relationship(
    "AlternativeInvestment", back_populates="user", cascade="all, delete-orphan"
)

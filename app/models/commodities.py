"""
Commodities & Precious Metals Models.
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


class CommodityType(str, Enum):
    GOLD = "gold"
    SILVER = "silver"
    PLATINUM = "platinum"
    OIL = "oil"
    NATURAL_GAS = "natural_gas"
    AGRICULTURAL = "agricultural"
    OTHER = "other"


class PositionType(str, Enum):
    LONG = "long"
    SHORT = "short"


class CommodityPosition(Base):
    """Commodity holding (physical or ETF)."""

    __tablename__ = "commodity_positions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    commodity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ticker: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Position details
    quantity: Mapped[float] = mapped_column(Numeric(16, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="shares")  # oz, g, barrel, shares

    # Pricing
    purchase_price: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    current_price: Mapped[Optional[float]] = mapped_column(Numeric(16, 4), nullable=True)
    market_value: Mapped[Optional[float]] = mapped_column(Numeric(16, 4), nullable=True)

    # P&L
    unrealized_pnl: Mapped[Optional[float]] = mapped_column(Numeric(16, 4), nullable=True)

    # Metadata
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="commodity_positions")


class FuturesContract(Base):
    """Futures contract tracking."""

    __tablename__ = "futures_contracts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    commodity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ticker: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Contract details
    contract_size: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    contract_month: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g. "2026-06"
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
    position_type: Mapped[str] = mapped_column(String(10), default="long")  # long/short

    # Pricing
    entry_price: Mapped[float] = mapped_column(Numeric(16, 4), nullable=False)
    current_price: Mapped[Optional[float]] = mapped_column(Numeric(16, 4), nullable=True)
    market_value: Mapped[Optional[float]] = mapped_column(Numeric(16, 4), nullable=True)

    # Margin
    margin_required: Mapped[Optional[float]] = mapped_column(Numeric(16, 4), nullable=True)

    # P&L
    realized_pnl: Mapped[Optional[float]] = mapped_column(Numeric(16, 4), nullable=True)
    unrealized_pnl: Mapped[Optional[float]] = mapped_column(Numeric(16, 4), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="futures_contracts")

"""
Options Tracking & Greek Letters Models
"""

import uuid
from datetime import datetime
from typing import Optional, Literal
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Numeric, Float, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OptionContract(Base):
    """Option contract model (stores reference data for options)."""

    __tablename__ = "option_contracts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    underlying_symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    strike_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    option_type: Mapped[str] = mapped_column(String(4), nullable=False)  # 'CALL' or 'PUT'
    exchange: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OptionPosition(Base):
    """User's option position in portfolio."""

    __tablename__ = "option_positions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    underlying_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    strike_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    option_type: Mapped[str] = mapped_column(String(4), nullable=False)  # 'CALL' or 'PUT'
    quantity: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)  # positive=long, negative=short
    premium: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)  # premium per share
    open_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    close_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="option_positions")

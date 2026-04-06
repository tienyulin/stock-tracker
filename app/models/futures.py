"""
Futures & Derivatives Models
"""

import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class FuturesPosition(Base):
    """User's futures position."""

    __tablename__ = "futures_positions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    contract_size: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=1)
    entry_price: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    current_price: Mapped[float] = mapped_column(Numeric(12, 4), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    position_type: Mapped[str] = mapped_column(String(10), nullable=False)  # LONG or SHORT
    entry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    margin_required: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    maintenance_margin: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    realized_pnl: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    broker: Mapped[str] = mapped_column(String(50), nullable=True)
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", onupdate="now()")

    def calculate_unrealized_pnl(self) -> float:
        """Calculate unrealized P&L."""
        if self.current_price is None:
            return 0.0
        price_diff = float(self.current_price) - float(self.entry_price)
        if self.position_type == "LONG":
            return price_diff * float(self.contract_size) * self.quantity
        else:
            return -price_diff * float(self.contract_size) * self.quantity


class FuturesContract(Base):
    """Reference data for futures contracts."""

    __tablename__ = "futures_contracts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False)
    contract_size: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    tick_size: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False)
    month_codes: Mapped[str] = mapped_column(String(20), nullable=True)  # F,G,H,J,K,M,N,Q,U,V,X,Z
    settlement: Mapped[str] = mapped_column(String(10), nullable=True)  # CASH or PHYSICAL
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class FuturesPriceAlert(Base):
    """Price alerts for futures positions."""

    __tablename__ = "futures_price_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PRICE_ABOVE, PRICE_BELOW, EXPIRY_WARNING
    threshold_price: Mapped[float] = mapped_column(Numeric(12, 4), nullable=True)
    days_before_expiry: Mapped[int] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")

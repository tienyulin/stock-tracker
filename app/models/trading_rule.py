"""
SQLAlchemy models for Automated Trading Rules.
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


class RuleStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    FAILED = "failed"


class RuleType(str, Enum):
    PRICE_TRIGGER = "price_trigger"       # Buy/sell when price crosses threshold
    INDICATOR_SIGNAL = "indicator_signal"  # Buy/sell based on RSI/MACD/MA
    REBALANCE = "rebalance"                # Portfolio rebalancing
    SCHEDULE = "schedule"                  # Time-based execution
    AI_SIGNAL = "ai_signal"                # AI-generated signal execution
    DIVIDEND_REINVEST = "dividend_reinvest"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"


class TradingRule(Base):
    """Automated trading rule definition."""

    __tablename__ = "trading_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Rule definition
    rule_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=RuleStatus.ACTIVE.value)

    # Trigger conditions (stored as JSON in payload)
    symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    target_quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # % of portfolio

    # Order parameters
    order_type: Mapped[str] = mapped_column(String(20), default=OrderType.MARKET.value)
    limit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stop_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Execution constraints
    max_order_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Max $ per trade
    max_daily_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)   # Max daily loss $
    broker_connection_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Scheduling
    schedule_cron: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Cron expression
    schedule_interval_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # State
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="trading_rules")
    executions: Mapped[list["AutomationLog"]] = relationship(
        "AutomationLog", back_populates="rule", cascade="all, delete-orphan"
    )

    class Config:
        from_attributes = True


class AutomationLog(Base):
    """Log of automated trading rule executions."""

    __tablename__ = "automation_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trading_rules.id", ondelete="CASCADE"), nullable=True
    )

    # Execution details
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    trigger_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Why triggered
    action_taken: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "buy", "sell", "rebalance"

    # Order details
    symbol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    order_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    order_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Outcome
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/success/failed/skipped
    broker_order_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    rule: Mapped[Optional["TradingRule"]] = relationship("TradingRule", back_populates="executions")

    class Config:
        from_attributes = True


class BrokerConnectionExtended(Base):
    """Extended broker connection with trading permissions."""

    __tablename__ = "broker_connections_ext"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    brokerage: Mapped[str] = mapped_column(String(50), nullable=False)
    account_id: Mapped[str] = mapped_column(String(100), nullable=False)
    account_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # OAuth tokens (encrypted in production)
    encrypted_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    encrypted_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Capabilities
    can_trade: Mapped[bool] = mapped_column(Boolean, default=False)
    can_read_positions: Mapped[bool] = mapped_column(Boolean, default=True)
    can_withdraw: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="connected")
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_trade_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="broker_connections_ext")

    class Config:
        from_attributes = True


# Add relationships to User model
User.trading_rules: Mapped[list["TradingRule"]] = relationship(
    "TradingRule", back_populates="user", cascade="all, delete-orphan"
)
User.broker_connections_ext: Mapped[list["BrokerConnectionExtended"]] = relationship(
    "BrokerConnectionExtended", back_populates="user", cascade="all, delete-orphan"
)

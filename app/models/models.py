"""
SQLAlchemy models for Stock Tracker.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    line_notify_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    discord_webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    watchlists: Mapped[list["Watchlist"]] = relationship(
        "Watchlist", back_populates="user", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="user", cascade="all, delete-orphan"
    )
    holdings: Mapped[list["UserHolding"]] = relationship(
        "UserHolding", back_populates="user", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list["ApiKey"]] = relationship(
        "ApiKey", back_populates="user", cascade="all, delete-orphan"
    )
    # Social features relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    followers: Mapped[list["Follow"]] = relationship(
        "Follow", foreign_keys="Follow.following_id", back_populates="following_user"
    )
    following: Mapped[list["Follow"]] = relationship(
        "Follow", foreign_keys="Follow.follower_id", back_populates="follower_user"
    )
    trade_activities: Mapped[list["TradeActivity"]] = relationship(
        "TradeActivity", back_populates="user", cascade="all, delete-orphan"
    )
    leaderboard_entries: Mapped[list["LeaderboardEntry"]] = relationship(
        "LeaderboardEntry", back_populates="user", cascade="all, delete-orphan"
    )


class Watchlist(Base):
    """Watchlist model."""

    __tablename__ = "watchlists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="watchlists")
    items: Mapped[list["WatchlistItem"]] = relationship(
        "WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan"
    )


class WatchlistItem(Base):
    """Watchlist item model."""

    __tablename__ = "watchlist_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("watchlists.id", ondelete="CASCADE"),
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    watchlist: Mapped["Watchlist"] = relationship("Watchlist", back_populates="items")


class Alert(Base):
    """Alert model."""

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    condition_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'above', 'below', 'change_pct'
    threshold: Mapped[float] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="alerts")
    notifications: Mapped[list["AlertNotification"]] = relationship(
        "AlertNotification", back_populates="alert", cascade="all, delete-orphan"
    )


class AlertNotification(Base):
    """Alert notification model."""

    __tablename__ = "alert_notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'telegram', 'email', 'push'
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # 'pending', 'sent', 'failed'
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    alert: Mapped["Alert"] = relationship("Alert", back_populates="notifications")


class UserHolding(Base):
    """User stock holding model."""

    __tablename__ = "user_holdings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[float] = mapped_column(nullable=False)
    avg_cost: Mapped[float] = mapped_column(nullable=False)  # average cost per share
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False, default="STOCK")
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dividend_yield: Mapped[Optional[float]] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    dividend_frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="NONE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="holdings")


class ApiKey(Base):
    """API Key model for rate limiting and authentication."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)  # First 8 chars for identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Postman", "Trading Bot"
    rate_limit: Mapped[int] = mapped_column(default=100)  # requests per minute
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")

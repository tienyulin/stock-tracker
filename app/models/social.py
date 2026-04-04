"""
SQLAlchemy models for Social Investing features.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Float, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.models import User


class UserProfile(Base):
    """Extended user profile for social features."""

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_profile_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_portfolio_public: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_followers: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")
    followers: Mapped[list["Follow"]] = relationship(
        "Follow", foreign_keys="Follow.following_id", back_populates="following_user", cascade="all, delete-orphan"
    )
    following: Mapped[list["Follow"]] = relationship(
        "Follow", foreign_keys="Follow.follower_id", back_populates="follower_user", cascade="all, delete-orphan"
    )


class Follow(Base):
    """Follow relationship between users."""

    __tablename__ = "follows"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    follower_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    following_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    follower_user: Mapped["User"] = relationship("User", foreign_keys=[follower_id], back_populates="following")
    following_user: Mapped["User"] = relationship("User", foreign_keys=[following_id], back_populates="followers")

    # Unique constraint to prevent duplicate follows
    __table_args__ = (
        # Unique together follower + following
    )


class TradeActivity(Base):
    """Public trade activity for social features."""

    __tablename__ = "trade_activities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    activity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'buy', 'sell', 'dividend'
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[Optional[float]] = mapped_column(nullable=True)
    price: Mapped[Optional[float]] = mapped_column(nullable=True)
    total_value: Mapped[Optional[float]] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="trade_activities")


class LeaderboardEntry(Base):
    """Cached leaderboard entries for performance tracking."""

    __tablename__ = "leaderboard_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # '1w', '1m', '3m', '1y', 'all'
    total_return: Mapped[float] = mapped_column(Float, default=0.0)
    total_return_pct: Mapped[float] = mapped_column(Float, default=0.0)
    rank: Mapped[int] = mapped_column(Integer, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="leaderboard_entries")

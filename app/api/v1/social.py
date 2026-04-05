"""
Social Investing API endpoints.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, desc
from sqlalchemy.orm import Session, joinedload

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models import User, UserProfile, Follow, TradeActivity, LeaderboardEntry
from app.models.models import UserHolding

router = APIRouter(prefix="/social", tags=["social"])


# Pydantic schemas
class ProfileSettings(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    is_profile_public: bool = False
    is_portfolio_public: bool = False
    allow_followers: bool = True


class ProfileResponse(BaseModel):
    user_id: uuid.UUID
    username: str
    display_name: Optional[str]
    bio: Optional[str]
    is_profile_public: bool
    is_portfolio_public: bool
    follower_count: int = 0
    following_count: int = 0

    class Config:
        from_attributes = True


class FollowResponse(BaseModel):
    id: uuid.UUID
    follower_id: uuid.UUID
    following_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class TradeActivityResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    username: str
    display_name: Optional[str]
    activity_type: str
    symbol: str
    quantity: Optional[float]
    price: Optional[float]
    total_value: Optional[float]
    currency: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LeaderboardEntryResponse(BaseModel):
    rank: int
    user_id: uuid.UUID
    username: str
    display_name: Optional[str]
    total_return: float
    total_return_pct: float
    period: str

    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    user_id: uuid.UUID
    username: str
    display_name: Optional[str]

    class Config:
        from_attributes = True


# Endpoints

@router.get("/profile/me", response_model=ProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's social profile."""
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    follower_count = db.query(func.count(Follow.id)).filter(
        Follow.following_id == current_user.id
    ).scalar()

    following_count = db.query(func.count(Follow.id)).filter(
        Follow.follower_id == current_user.id
    ).scalar()

    return ProfileResponse(
        user_id=current_user.id,
        username=current_user.username,
        display_name=profile.display_name if profile else None,
        bio=profile.bio if profile else None,
        is_profile_public=profile.is_profile_public if profile else False,
        is_portfolio_public=profile.is_portfolio_public if profile else False,
        follower_count=follower_count or 0,
        following_count=following_count or 0,
    )


@router.put("/profile/me", response_model=ProfileResponse)
def update_my_profile(
    settings: ProfileSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's social profile settings."""
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if settings.display_name is not None:
        profile.display_name = settings.display_name
    if settings.bio is not None:
        profile.bio = settings.bio
    if settings.is_profile_public is not None:
        profile.is_profile_public = settings.is_profile_public
    if settings.is_portfolio_public is not None:
        profile.is_portfolio_public = settings.is_portfolio_public
    if settings.allow_followers is not None:
        profile.allow_followers = settings.allow_followers

    db.commit()
    db.refresh(profile)

    follower_count = db.query(func.count(Follow.id)).filter(
        Follow.following_id == current_user.id
    ).scalar()

    following_count = db.query(func.count(Follow.id)).filter(
        Follow.follower_id == current_user.id
    ).scalar()

    return ProfileResponse(
        user_id=current_user.id,
        username=current_user.username,
        display_name=profile.display_name,
        bio=profile.bio,
        is_profile_public=profile.is_profile_public,
        is_portfolio_public=profile.is_portfolio_public,
        follower_count=follower_count or 0,
        following_count=following_count or 0,
    )


@router.get("/users/{user_id}/profile", response_model=ProfileResponse)
def get_user_profile(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a user's public profile."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user_id
    ).first()

    # Check if profile is public or if current user follows them
    is_following = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()

    if profile and not profile.is_profile_public and not is_following:
        raise HTTPException(status_code=403, detail="This profile is private")

    follower_count = db.query(func.count(Follow.id)).filter(
        Follow.following_id == user_id
    ).scalar()

    following_count = db.query(func.count(Follow.id)).filter(
        Follow.follower_id == user_id
    ).scalar()

    return ProfileResponse(
        user_id=user.id,
        username=user.username,
        display_name=profile.display_name if profile else None,
        bio=profile.bio if profile else None,
        is_profile_public=profile.is_profile_public if profile else False,
        is_portfolio_public=profile.is_portfolio_public if profile else False,
        follower_count=follower_count or 0,
        following_count=following_count or 0,
    )


@router.post("/follow/{user_id}", response_model=FollowResponse)
def follow_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Follow a user."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if target user allows followers
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user_id
    ).first()

    if profile and not profile.allow_followers:
        raise HTTPException(status_code=403, detail="This user does not allow followers")

    # Check if already following
    existing = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already following this user")

    follow = Follow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    db.commit()
    db.refresh(follow)

    return follow


@router.delete("/follow/{user_id}")
def unfollow_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unfollow a user."""
    follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()

    if not follow:
        raise HTTPException(status_code=404, detail="Not following this user")

    db.delete(follow)
    db.commit()

    return {"message": "Unfollowed successfully"}


@router.get("/following", response_model=list[UserSummary])
def get_following(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of users current user is following."""
    follows = db.query(Follow).filter(
        Follow.follower_id == current_user.id
    ).options(joinedload(Follow.following_user)).all()

    result = []
    for f in follows:
        following_user = f.following_user
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == following_user.id
        ).first()
        result.append(UserSummary(
            user_id=following_user.id,
            username=following_user.username,
            display_name=profile.display_name if profile else None
        ))

    return result


@router.get("/followers", response_model=list[UserSummary])
def get_followers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of users following current user."""
    follows = db.query(Follow).filter(
        Follow.following_id == current_user.id
    ).options(joinedload(Follow.follower_user)).all()

    result = []
    for f in follows:
        follower_user = f.follower_user
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == follower_user.id
        ).first()
        result.append(UserSummary(
            user_id=follower_user.id,
            username=follower_user.username,
            display_name=profile.display_name if profile else None
        ))

    return result


@router.post("/activity", response_model=TradeActivityResponse)
def create_trade_activity(
    activity_type: str = Field(..., description="Type: buy, sell, dividend"),
    symbol: str = Field(..., description="Stock symbol"),
    quantity: Optional[float] = None,
    price: Optional[float] = None,
    total_value: Optional[float] = None,
    currency: str = "USD",
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a public trade activity (e.g., when user buys/sells a stock)."""
    if activity_type not in ["buy", "sell", "dividend"]:
        raise HTTPException(status_code=400, detail="Invalid activity type")

    # Check if user's portfolio is public
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    if not profile or not profile.is_portfolio_public:
        raise HTTPException(
            status_code=403,
            detail="Your portfolio must be public to share trade activities"
        )

    activity = TradeActivity(
        user_id=current_user.id,
        activity_type=activity_type,
        symbol=symbol.upper(),
        quantity=quantity,
        price=price,
        total_value=total_value,
        currency=currency,
        notes=notes,
        is_public=True
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)

    return TradeActivityResponse(
        id=activity.id,
        user_id=current_user.id,
        username=current_user.username,
        display_name=profile.display_name if profile else None,
        activity_type=activity.activity_type,
        symbol=activity.symbol,
        quantity=activity.quantity,
        price=activity.price,
        total_value=activity.total_value,
        currency=activity.currency,
        notes=activity.notes,
        created_at=activity.created_at
    )


@router.get("/activity/feed", response_model=list[TradeActivityResponse])
def get_activity_feed(
    period: str = "all",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get public activity feed from followed users."""
    # Get list of users current user is following
    following_ids = db.query(Follow.following_id).filter(
        Follow.follower_id == current_user.id
    ).all()
    following_ids = [f[0] for f in following_ids]

    if not following_ids:
        return []

    # Build query
    query = db.query(TradeActivity, User).join(
        User, TradeActivity.user_id == User.id
    ).filter(
        TradeActivity.user_id.in_(following_ids),
        TradeActivity.is_public.is_(True)
    )

    # Filter by period
    if period == "1w":
        cutoff = datetime.utcnow() - timedelta(days=7)
        query = query.filter(TradeActivity.created_at >= cutoff)
    elif period == "1m":
        cutoff = datetime.utcnow() - timedelta(days=30)
        query = query.filter(TradeActivity.created_at >= cutoff)
    elif period == "3m":
        cutoff = datetime.utcnow() - timedelta(days=90)
        query = query.filter(TradeActivity.created_at >= cutoff)

    query = query.order_by(desc(TradeActivity.created_at)).limit(50)

    results = []
    for activity, user in query.all():
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user.id
        ).first()
        results.append(TradeActivityResponse(
            id=activity.id,
            user_id=user.id,
            username=user.username,
            display_name=profile.display_name if profile else None,
            activity_type=activity.activity_type,
            symbol=activity.symbol,
            quantity=activity.quantity,
            price=activity.price,
            total_value=activity.total_value,
            currency=activity.currency,
            notes=activity.notes,
            created_at=activity.created_at
        ))

    return results


@router.get("/leaderboard", response_model=list[LeaderboardEntryResponse])
def get_leaderboard(
    period: str = "1m",
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance leaderboard."""
    if period not in ["1w", "1m", "3m", "1y", "all"]:
        raise HTTPException(status_code=400, detail="Invalid period")

    # Get public profiles
    public_user_ids = db.query(UserProfile.user_id).filter(
        UserProfile.is_portfolio_public.is_(True)
    ).subquery()

    # Calculate performance for each user (simplified calculation)
    # In production, this would use actual historical portfolio data
    holdings = db.query(
        UserHolding.user_id,
        func.sum(UserHolding.quantity * UserHolding.avg_cost).label("total_invested")
    ).filter(
        UserHolding.user_id.in_(public_user_ids)
    ).group_by(UserHolding.user_id).all()

    user_performance = []
    for user_id, total_invested in holdings:
        if not total_invested or total_invested <= 0:
            continue

        # Simplified: assume 10% random return for demo
        # In production: calculate actual portfolio performance
        import random
        total_return = total_invested * (random.uniform(-0.15, 0.25) if True else 0.1)
        total_return_pct = (total_return / total_invested) * 100

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            continue

        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        user_performance.append({
            "user_id": user_id,
            "username": user.username,
            "display_name": profile.display_name if profile else None,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "period": period
        })

    # Sort by return percentage
    user_performance.sort(key=lambda x: x["total_return_pct"], reverse=True)

    # Assign ranks
    results = []
    for i, perf in enumerate(user_performance[:limit]):
        results.append(LeaderboardEntryResponse(
            rank=i + 1,
            user_id=perf["user_id"],
            username=perf["username"],
            display_name=perf["display_name"],
            total_return=round(perf["total_return"], 2),
            total_return_pct=round(perf["total_return_pct"], 2),
            period=perf["period"]
        ))

    return results


@router.get("/users/{user_id}/holdings", response_model=list[dict])
def get_user_holdings(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a user's public holdings."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = db.query(UserProfile).filter(
        UserProfile.user_id == user_id
    ).first()

    if not profile or not profile.is_portfolio_public:
        # Check if current user follows them
        is_following = db.query(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        ).first()

        if not is_following:
            raise HTTPException(status_code=403, detail="This user's portfolio is private")

    holdings = db.query(UserHolding).filter(
        UserHolding.user_id == user_id
    ).all()

    return [
        {
            "symbol": h.symbol,
            "quantity": h.quantity,
            "avg_cost": h.avg_cost,
            "asset_type": h.asset_type,
            "sector": h.sector,
            "currency": h.currency
        }
        for h in holdings
    ]

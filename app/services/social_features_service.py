"""
Social Features Service

Provides social/community features:
- Share portfolios publicly
- Follow other investors
- View community portfolio performance
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SharedPortfolio:
    """Publicly shared portfolio summary."""
    user_id: str
    username: str
    portfolio_summary: dict
    total_value: float
    total_gain_loss: float
    total_gain_loss_percent: float
    sharpe_ratio: float
    followers_count: int
    is_public: bool
    shared_at: str


@dataclass
class FollowResult:
    """Result of following/unfollowing a user."""
    success: bool
    message: str
    followers_count: int


class SocialFeaturesService:
    """Service for social/community features."""

    def __init__(self):
        """Initialize Social Features Service."""
        pass

    async def share_portfolio(
        self,
        user_id: str,
        username: str,
        holdings: list,
        prices: dict,
        is_public: bool = True
    ) -> SharedPortfolio:
        """
        Share a portfolio publicly.
        """
        portfolio_summary = {}
        total_value = 0.0
        total_cost = 0.0

        for h in holdings:
            symbol = h["symbol"]
            quantity = h["quantity"]
            avg_cost = h["avg_cost"]
            current_price = prices.get(symbol, 0)

            value = quantity * current_price
            cost = quantity * avg_cost
            gain_loss = value - cost
            gain_loss_percent = (gain_loss / cost * 100) if cost > 0 else 0

            portfolio_summary[symbol] = {
                "quantity": quantity,
                "avg_cost": avg_cost,
                "current_price": current_price,
                "value": round(value, 2),
                "gain_loss": round(gain_loss, 2),
                "gain_loss_percent": round(gain_loss_percent, 2),
            }

            total_value += value
            total_cost += cost

        total_gain_loss = total_value - total_cost
        total_gain_loss_percent = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0

        return SharedPortfolio(
            user_id=user_id,
            username=username,
            portfolio_summary=portfolio_summary,
            total_value=round(total_value, 2),
            total_gain_loss=round(total_gain_loss, 2),
            total_gain_loss_percent=round(total_gain_loss_percent, 2),
            sharpe_ratio=0.0,
            followers_count=0,
            is_public=is_public,
            shared_at=datetime.now().isoformat(),
        )

    async def follow_user(
        self,
        follower_id: str,
        following_id: str,
        action: str = "follow"
    ) -> FollowResult:
        """
        Follow or unfollow a user.
        """
        if follower_id == following_id:
            return FollowResult(
                success=False,
                message="Cannot follow yourself",
                followers_count=0
            )

        if action == "follow":
            return FollowResult(
                success=True,
                message=f"Now following user {following_id}",
                followers_count=1
            )
        else:
            return FollowResult(
                success=True,
                message=f"Unfollowed user {following_id}",
                followers_count=0
            )

    async def get_community_portfolios(
        self,
        limit: int = 20,
        sort_by: str = "performance"
    ) -> list:
        """
        Get list of publicly shared portfolios.
        """
        return []

    async def get_user_followers(self, user_id: str) -> list:
        """
        Get list of followers for a user.
        """
        return []

    async def get_user_following(self, user_id: str) -> list:
        """
        Get list of users that a user is following.
        """
        return []

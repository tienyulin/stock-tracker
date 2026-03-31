"""
Watchlist Service - Personal Watchlist Feature

Provides watchlist management for users to track stocks.
"""

import uuid
from dataclasses import dataclass


from app.exceptions import ValidationError


@dataclass
class WatchlistItem:
    """Watchlist item data model."""

    id: str
    user_id: str
    symbol: str
    name: str
    added_at: int


class WatchlistService:
    """Service for managing user watchlists."""

    MAX_WATCHLIST_SIZE = 50

    def __init__(self):
        """Initialize Watchlist Service."""
        self._watchlists: dict[str, list[WatchlistItem]] = {}

    async def _validate_user(self, user_id: str) -> bool:
        """
        Validate user exists.

        Args:
            user_id: User ID.

        Returns:
            True if valid.
        """
        if not user_id:
            raise ValidationError("Invalid user ID")
        return True

    def _get_watchlist(self, user_id: str) -> list[WatchlistItem]:
        """Get or create user's watchlist."""
        if user_id not in self._watchlists:
            self._watchlists[user_id] = []
        return self._watchlists[user_id]

    async def add_stock(self, user_id: str, symbol: str, name: str) -> WatchlistItem:
        """
        Add a stock to user's watchlist.

        Args:
            user_id: User ID.
            symbol: Stock symbol.
            name: Stock name.

        Returns:
            WatchlistItem created.

        Raises:
            ValidationError: If invalid input.
            Exception: If stock already in watchlist or limit reached.
        """
        await self._validate_user(user_id)

        if not symbol:
            raise ValidationError("Invalid symbol")

        watchlist = self._get_watchlist(user_id)

        # Check if already exists
        if any(item.symbol == symbol for item in watchlist):
            raise Exception(f"Stock {symbol} already in watchlist")

        # Check limit
        if len(watchlist) >= self.MAX_WATCHLIST_SIZE:
            raise Exception(
                f"Watchlist maximum limit ({self.MAX_WATCHLIST_SIZE}) reached"
            )

        item = WatchlistItem(
            id=str(uuid.uuid4()),
            user_id=user_id,
            symbol=symbol.upper(),
            name=name,
            added_at=0,  # Would normally be timestamp
        )

        watchlist.append(item)
        return item

    async def remove_stock(self, user_id: str, symbol: str) -> bool:
        """
        Remove a stock from user's watchlist.

        Args:
            user_id: User ID.
            symbol: Stock symbol.

        Returns:
            True if removed.

        Raises:
            Exception: If stock not found.
        """
        await self._validate_user(user_id)

        watchlist = self._get_watchlist(user_id)

        for i, item in enumerate(watchlist):
            if item.symbol == symbol.upper():
                watchlist.pop(i)
                return True

        raise Exception(f"Stock {symbol} not found in watchlist")

    async def get_watchlist(self, user_id: str) -> list[WatchlistItem]:
        """
        Get user's watchlist.

        Args:
            user_id: User ID.

        Returns:
            List of WatchlistItems.
        """
        await self._validate_user(user_id)
        return self._get_watchlist(user_id).copy()

    async def is_tracking(self, user_id: str, symbol: str) -> bool:
        """
        Check if stock is in user's watchlist.

        Args:
            user_id: User ID.
            symbol: Stock symbol.

        Returns:
            True if tracking.
        """
        await self._validate_user(user_id)

        watchlist = self._get_watchlist(user_id)
        return any(item.symbol == symbol.upper() for item in watchlist)

    async def clear_watchlist(self, user_id: str) -> bool:
        """
        Clear all stocks from user's watchlist.

        Args:
            user_id: User ID.

        Returns:
            True if cleared.
        """
        await self._validate_user(user_id)

        if user_id in self._watchlists:
            self._watchlists[user_id].clear()
        return True

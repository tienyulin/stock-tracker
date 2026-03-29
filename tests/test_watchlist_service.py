"""
Tests for Watchlist Service - Personal Watchlist Feature
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.watchlist_service import WatchlistService, WatchlistItem


class TestWatchlistItem:
    """Test data model for watchlist item."""

    def test_watchlist_item_creation(self):
        item = WatchlistItem(
            id="uuid-123",
            user_id="user-1",
            symbol="AAPL",
            name="Apple Inc.",
            added_at=1700000000
        )
        assert item.symbol == "AAPL"
        assert item.name == "Apple Inc."
        assert item.user_id == "user-1"


class TestWatchlistService:
    """Test Watchlist Service for personal watchlist management."""

    @pytest.fixture
    def service(self):
        return WatchlistService()

    @pytest.fixture
    def mock_user_id(self):
        return "user-123"

    @pytest.mark.asyncio
    async def test_add_stock_to_watchlist(self, service, mock_user_id):
        """Test adding a stock to watchlist."""
        with patch.object(service, '_validate_user', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True

            item = await service.add_stock(mock_user_id, "AAPL", "Apple Inc.")

            assert item.symbol == "AAPL"
            assert item.name == "Apple Inc."
            assert item.user_id == mock_user_id

    @pytest.mark.asyncio
    async def test_add_duplicate_stock(self, service, mock_user_id):
        """Test adding duplicate stock to watchlist raises error."""
        with patch.object(service, '_validate_user', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True
            await service.add_stock(mock_user_id, "AAPL", "Apple Inc.")

            with pytest.raises(Exception, match="already in watchlist"):
                await service.add_stock(mock_user_id, "AAPL", "Apple Inc.")

    @pytest.mark.asyncio
    async def test_remove_stock_from_watchlist(self, service, mock_user_id):
        """Test removing a stock from watchlist."""
        with patch.object(service, '_validate_user', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True
            await service.add_stock(mock_user_id, "AAPL", "Apple Inc.")

            result = await service.remove_stock(mock_user_id, "AAPL")

            assert result is True

    @pytest.mark.asyncio
    async def test_remove_nonexistent_stock(self, service, mock_user_id):
        """Test removing non-existent stock raises error."""
        with patch.object(service, '_validate_user', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True

            with pytest.raises(Exception, match="not found in watchlist"):
                await service.remove_stock(mock_user_id, "INVALID")

    @pytest.mark.asyncio
    async def test_get_watchlist(self, service, mock_user_id):
        """Test getting user's watchlist."""
        with patch.object(service, '_validate_user', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True
            await service.add_stock(mock_user_id, "AAPL", "Apple Inc.")
            await service.add_stock(mock_user_id, "GOOGL", "Alphabet Inc.")

            watchlist = await service.get_watchlist(mock_user_id)

            assert len(watchlist) == 2
            symbols = {item.symbol for item in watchlist}
            assert symbols == {"AAPL", "GOOGL"}

    @pytest.mark.asyncio
    async def test_get_watchlist_empty(self, service, mock_user_id):
        """Test getting empty watchlist."""
        with patch.object(service, '_validate_user', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True

            watchlist = await service.get_watchlist(mock_user_id)

            assert len(watchlist) == 0

    @pytest.mark.asyncio
    async def test_is_tracking_stock(self, service, mock_user_id):
        """Test checking if stock is in watchlist."""
        with patch.object(service, '_validate_user', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True
            await service.add_stock(mock_user_id, "AAPL", "Apple Inc.")

            assert await service.is_tracking(mock_user_id, "AAPL") is True
            assert await service.is_tracking(mock_user_id, "GOOGL") is False

    @pytest.mark.asyncio
    async def test_watchlist_limit(self, service, mock_user_id):
        """Test watchlist has maximum limit."""
        with patch.object(service, '_validate_user', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = True

            # Add 50 stocks (max limit)
            for i in range(50):
                await service.add_stock(mock_user_id, f"STOCK{i}", f"Stock {i}")

            # Try to add 51st stock
            with pytest.raises(Exception, match="maximum limit"):
                await service.add_stock(mock_user_id, "STOCK51", "Stock 51")

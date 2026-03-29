"""
Tests for Stock Service - Basic Stock Price Query
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.stock_service import StockService, StockInfo, PriceData


class TestStockInfo:
    """Test data model for stock information."""

    def test_stock_info_creation(self):
        info = StockInfo(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            currency="USD"
        )
        assert info.symbol == "AAPL"
        assert info.name == "Apple Inc."
        assert info.exchange == "NASDAQ"
        assert info.currency == "USD"


class TestPriceData:
    """Test data model for price data."""

    def test_price_data_creation(self):
        price = PriceData(
            symbol="AAPL",
            current_price=150.25,
            open_price=149.50,
            high_price=151.00,
            low_price=148.75,
            previous_close=149.00,
            volume=1000000
        )
        assert price.symbol == "AAPL"
        assert price.current_price == 150.25
        assert price.change_percent == pytest.approx(0.84, rel=0.01)


class TestStockService:
    """Test Stock Service for basic price queries."""

    @pytest.fixture
    def service(self):
        return StockService()

    @pytest.fixture
    def mock_quote_response(self):
        return {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
            "exchange": "NASDAQ",
            "currency": "USD",
            "regularMarketPrice": 150.25,
            "regularMarketOpen": 149.50,
            "regularMarketDayHigh": 151.00,
            "regularMarketDayLow": 148.75,
            "regularMarketPreviousClose": 149.00,
            "regularMarketVolume": 1000000
        }

    @pytest.mark.asyncio
    async def test_get_stock_info_success(self, service, mock_quote_response):
        """Test successful stock info retrieval."""
        with patch.object(service, '_fetch_quote', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_quote_response

            info = await service.get_stock_info("AAPL")

            assert info.symbol == "AAPL"
            assert info.name == "Apple Inc."
            assert info.exchange == "NASDAQ"
            mock_fetch.assert_called_once_with("AAPL")

    @pytest.mark.asyncio
    async def test_get_stock_info_not_found(self, service):
        """Test stock info for non-existent symbol."""
        with patch.object(service, '_fetch_quote', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            info = await service.get_stock_info("INVALID")

            assert info is None

    @pytest.mark.asyncio
    async def test_get_price_data_success(self, service, mock_quote_response):
        """Test successful price data retrieval."""
        with patch.object(service, '_fetch_quote', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_quote_response

            price = await service.get_price_data("AAPL")

            assert price.symbol == "AAPL"
            assert price.current_price == 150.25
            assert price.open_price == 149.50
            assert price.high_price == 151.00
            assert price.low_price == 148.75
            assert price.previous_close == 149.00
            assert price.volume == 1000000

    @pytest.mark.asyncio
    async def test_get_price_data_not_found(self, service):
        """Test price data for non-existent symbol."""
        with patch.object(service, '_fetch_quote', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            price = await service.get_price_data("INVALID")

            assert price is None

    @pytest.mark.asyncio
    async def test_get_multiple_quotes(self, service):
        """Test retrieving multiple stock quotes."""
        mock_responses = {
            "AAPL": {"symbol": "AAPL", "regularMarketPrice": 150.25},
            "GOOGL": {"symbol": "GOOGL", "regularMarketPrice": 140.50}
        }

        async def mock_fetch(symbol):
            return mock_responses.get(symbol)

        with patch.object(service, '_fetch_quote', side_effect=mock_fetch):
            prices = await service.get_multiple_quotes(["AAPL", "GOOGL"])

            assert len(prices) == 2
            assert prices["AAPL"].current_price == 150.25
            assert prices["GOOGL"].current_price == 140.50

    def test_validate_symbol_format(self, service):
        """Test symbol format validation."""
        assert service.validate_symbol("AAPL") is True
        assert service.validate_symbol("2330.TW") is True
        assert service.validate_symbol("") is False
        assert service.validate_symbol("A" * 20) is False

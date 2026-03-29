import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.yfinance_service import YFinanceService, StockQuote, StockHistory


class TestStockQuote:
    """Test data model for stock quote."""

    def test_stock_quote_creation(self):
        quote = StockQuote(
            symbol="AAPL",
            price=150.25,
            volume=1000000,
            timestamp=1609459200
        )
        assert quote.symbol == "AAPL"
        assert quote.price == 150.25
        assert quote.volume == 1000000


class TestStockHistory:
    """Test data model for stock history."""

    def test_stock_history_creation(self):
        history = StockHistory(
            symbol="AAPL",
            timestamps=[1609459200, 1609545600],
            opens=[150.0, 151.0],
            highs=[152.0, 153.0],
            lows=[149.0, 150.0],
            closes=[151.0, 152.0],
            volumes=[1000000, 1100000]
        )
        assert history.symbol == "AAPL"
        assert len(history.closes) == 2


class TestYFinanceService:
    """Test YFinance service for stock data retrieval."""

    @pytest.fixture
    def service(self):
        return YFinanceService()

    @pytest.fixture
    def mock_quote_response(self):
        return {
            "chart": {
                "result": [{
                    "meta": {
                        "symbol": "AAPL",
                        "regularMarketPrice": 150.25,
                        "regularMarketVolume": 1000000
                    }
                }]
            }
        }

    @pytest.mark.asyncio
    async def test_get_quote_success(self, service, mock_quote_response):
        """Test successful quote retrieval."""
        with patch.object(service, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_quote_response

            quote = await service.get_quote("AAPL")

            assert quote.symbol == "AAPL"
            assert quote.price == 150.25
            assert quote.volume == 1000000
            mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_quote_not_found(self, service):
        """Test quote retrieval for non-existent symbol."""
        with patch.object(service, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"chart": {"result": None}}

            quote = await service.get_quote("INVALID")

            assert quote is None

    @pytest.mark.asyncio
    async def test_get_quote_network_error(self, service):
        """Test quote retrieval with network error."""
        with patch.object(service, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")

            with pytest.raises(Exception, match="Network error"):
                await service.get_quote("AAPL")

    @pytest.mark.asyncio
    async def test_get_history_success(self, service):
        """Test successful history retrieval."""
        mock_history_response = {
            "chart": {
                "result": [{
                    "timestamp": [1609459200, 1609545600],
                    "indicators": {
                        "quote": [{
                            "open": [150.0, 151.0],
                            "high": [152.0, 153.0],
                            "low": [149.0, 150.0],
                            "close": [151.0, 152.0],
                            "volume": [1000000, 1100000]
                        }]
                    }
                }]
            }
        }

        with patch.object(service, '_fetch', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_history_response

            history = await service.get_history("AAPL", period="1mo")

            assert history.symbol == "AAPL"
            assert len(history.closes) == 2
            assert history.closes[0] == 151.0

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, service):
        """Test retry mechanism on transient failure."""
        # Create a mock that fails twice then succeeds
        call_count = 0

        async def mock_fetch(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("Temporary connection error")
            return {
                "chart": {
                    "result": [{
                        "meta": {
                            "symbol": "AAPL",
                            "regularMarketPrice": 150.0,
                            "regularMarketVolume": 1000
                        }
                    }]
                }
            }

        # Patch the HTTP client get method to simulate network errors
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "chart": {
                "result": [{
                    "meta": {
                        "symbol": "AAPL",
                        "regularMarketPrice": 150.0,
                        "regularMarketVolume": 1000
                    }
                }]
            }
        }

        with patch('httpx.AsyncClient.get', side_effect=[
            httpx.ConnectError("Temporary error"),
            httpx.ConnectError("Temporary error"),
            mock_response
        ]):
            quote = await service.get_quote("AAPL")

            assert quote is not None
            assert quote.price == 150.0

    def test_validate_symbol(self, service):
        """Test symbol validation."""
        assert service.validate_symbol("AAPL") is True
        assert service.validate_symbol("2330.TW") is True
        assert service.validate_symbol("") is False
        assert service.validate_symbol("A" * 100) is False

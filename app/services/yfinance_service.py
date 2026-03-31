"""
Yahoo Finance API Service

Provides stock data retrieval from Yahoo Finance API.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

import httpx

from app.exceptions import (
    SymbolNotFoundError,
    NetworkError,
    RateLimitError,
    ValidationError,
)


@dataclass
class StockQuote:
    """Stock quote data model."""

    symbol: str
    price: float
    volume: int
    timestamp: Optional[int] = None
    market_state: Optional[str] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None


@dataclass
class StockHistory:
    """Stock historical data model."""

    symbol: str
    timestamps: list[int]
    opens: list[float]
    highs: list[float]
    lows: list[float]
    closes: list[float]
    volumes: list[int]


class YFinanceService:
    """Service for retrieving stock data from Yahoo Finance."""

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance"
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    def __init__(self, timeout: float = 10.0):
        """
        Initialize YFinance service.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": "Mozilla/5.0 (compatible; StockTracker/1.0)"},
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _fetch(self, url: str, params: Optional[dict] = None) -> dict:
        """
        Fetch data from Yahoo Finance API with retry logic.

        Args:
            url: API endpoint URL.
            params: Query parameters.

        Returns:
            JSON response data.

        Raises:
            NetworkError: On network failure.
            RateLimitError: On rate limit.
        """
        client = await self._get_client()
        last_error: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise SymbolNotFoundError(
                        f"Symbol not found: {params.get('symbol', 'unknown')}"
                    )
                elif e.response.status_code == 429:
                    raise RateLimitError("Yahoo Finance rate limit exceeded")
                else:
                    raise NetworkError(f"HTTP error: {e.response.status_code}")

            except httpx.RequestError as e:
                last_error = NetworkError(f"Request failed: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue
                raise last_error

        raise last_error or NetworkError("Unknown error")

    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate stock symbol format.

        Args:
            symbol: Stock symbol to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not symbol or len(symbol) > 10:
            return False

        # Allow alphanumeric, dots (for yahoo finance format), and dashes
        valid_chars = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-"
        )
        return all(c in valid_chars for c in symbol)

    async def get_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        Get real-time quote for a stock symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL", "2330.TW").

        Returns:
            StockQuote object or None if not found.

        Raises:
            ValidationError: If symbol format is invalid.
            NetworkError: On network failure.
            RateLimitError: On rate limit.
        """
        if not self.validate_symbol(symbol):
            raise ValidationError(f"Invalid symbol format: {symbol}")

        url = f"{self.BASE_URL}/chart/{symbol}"
        params = {"interval": "1d", "range": "1d", "symbol": symbol}

        data = await self._fetch(url, params)

        result = data.get("chart", {}).get("result")
        if not result:
            return None

        meta = result[0].get("meta", {})
        if not meta:
            return None

        return StockQuote(
            symbol=meta.get("symbol", symbol),
            price=meta.get("regularMarketPrice", 0.0),
            volume=meta.get("regularMarketVolume", 0),
            timestamp=int(meta.get("regularMarketTime", 0)),
            market_state=meta.get("marketState", "UNKNOWN"),
            change=meta.get("regularMarketChange", None),
            change_percent=meta.get("regularMarketChangePercent", None),
        )

    async def get_history(
        self, symbol: str, period: str = "1mo", interval: str = "1d"
    ) -> Optional[StockHistory]:
        """
        Get historical stock data.

        Args:
            symbol: Stock symbol.
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, 10y, ytd, max).
            interval: Data interval (1d, 1wk, 1mo).

        Returns:
            StockHistory object or None if not found.

        Raises:
            ValidationError: If symbol format is invalid.
            NetworkError: On network failure.
            RateLimitError: On rate limit.
        """
        if not self.validate_symbol(symbol):
            raise ValidationError(f"Invalid symbol format: {symbol}")

        url = f"{self.BASE_URL}/chart/{symbol}"
        params = {"interval": interval, "range": period, "symbol": symbol}

        data = await self._fetch(url, params)

        result = data.get("chart", {}).get("result")
        if not result or len(result) == 0:
            return None

        result_data = result[0]
        timestamps = result_data.get("timestamp", [])
        indicators = result_data.get("indicators", {})
        quote = indicators.get("quote", [{}])[0]

        return StockHistory(
            symbol=result_data.get("meta", {}).get("symbol", symbol),
            timestamps=timestamps,
            opens=quote.get("open", []),
            highs=quote.get("high", []),
            lows=quote.get("low", []),
            closes=quote.get("close", []),
            volumes=quote.get("volume", []),
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

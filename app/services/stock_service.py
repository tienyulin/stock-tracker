"""
Stock Service - Basic Stock Price Query

Provides stock information and price data retrieval with caching.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

from app.exceptions import ValidationError
from app.services.cache_service import stock_quote_cache


@dataclass
class StockInfo:
    """Stock basic information model."""

    symbol: str
    name: str
    exchange: str
    currency: str


@dataclass
class PriceData:
    """Stock price data model."""

    symbol: str
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    previous_close: float
    volume: int

    @property
    def change_percent(self) -> float:
        """Calculate price change percentage."""
        if self.previous_close == 0:
            return 0.0
        return ((self.current_price - self.previous_close) / self.previous_close) * 100


class StockService:
    """Service for stock information and price queries with caching."""

    def __init__(self):
        """Initialize Stock Service."""
        pass

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

        valid_chars = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.^-"
        )
        return all(c in valid_chars for c in symbol)

    async def _fetch_quote(self, symbol: str) -> Optional[dict]:
        """
        Fetch quote data from Yahoo Finance (with caching).

        Args:
            symbol: Stock symbol.

        Returns:
            Quote data dict or None if not found.
        """
        # Try cache first
        cache_key = f"quote:{symbol}"
        cached = await stock_quote_cache.get(cache_key)
        if cached is not None:
            return cached

        # Import here to avoid circular dependency
        from app.services.yfinance_service import YFinanceService

        async with YFinanceService() as yf:
            quote = await yf.get_quote(symbol)
            if quote is None:
                return None

            result = {
                "symbol": quote.symbol,
                "regularMarketPrice": quote.price,
                "regularMarketVolume": quote.volume,
            }

            # Cache the result
            await stock_quote_cache.set(cache_key, result, ttl=30.0)
            return result

    async def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """
        Get basic stock information.

        Args:
            symbol: Stock symbol.

        Returns:
            StockInfo object or None if not found.

        Raises:
            ValidationError: If symbol format is invalid.
        """
        if not self.validate_symbol(symbol):
            raise ValidationError(f"Invalid symbol format: {symbol}")

        quote = await self._fetch_quote(symbol)
        if quote is None:
            return None

        return StockInfo(
            symbol=quote.get("symbol", symbol),
            name=quote.get("shortName", quote.get("symbol", symbol)),
            exchange=quote.get("exchange", "UNKNOWN"),
            currency=quote.get("currency", "USD"),
        )

    async def get_price_data(self, symbol: str) -> Optional[PriceData]:
        """
        Get detailed price data for a stock.

        Args:
            symbol: Stock symbol.

        Returns:
            PriceData object or None if not found.

        Raises:
            ValidationError: If symbol format is invalid.
        """
        if not self.validate_symbol(symbol):
            raise ValidationError(f"Invalid symbol format: {symbol}")

        quote = await self._fetch_quote(symbol)
        if quote is None:
            return None

        return PriceData(
            symbol=quote.get("symbol", symbol),
            current_price=quote.get("regularMarketPrice", 0.0),
            open_price=quote.get("regularMarketOpen", 0.0),
            high_price=quote.get("regularMarketDayHigh", 0.0),
            low_price=quote.get("regularMarketDayLow", 0.0),
            previous_close=quote.get("regularMarketPreviousClose", 0.0),
            volume=quote.get("regularMarketVolume", 0),
        )

    async def get_multiple_quotes(self, symbols: list[str]) -> dict[str, PriceData]:
        """
        Get price data for multiple stocks (with caching).

        Args:
            symbols: List of stock symbols.

        Returns:
            Dict mapping symbol to PriceData.
        """
        # Use asyncio.gather for concurrent fetching
        async def fetch_one(symbol: str) -> tuple[str, Optional[PriceData]]:
            price = await self.get_price_data(symbol)
            return (symbol, price)

        results_list = await asyncio.gather(*[fetch_one(s) for s in symbols])
        
        return {
            symbol: price 
            for symbol, price in results_list 
            if price is not None
        }

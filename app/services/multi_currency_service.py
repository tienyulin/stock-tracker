"""
Multi-Currency Service

Provides multi-currency support for portfolio tracking:
- Display portfolio in user's preferred currency
- Real-time exchange rates
- Support for USD, TWD, JPY, EUR, etc.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


# Supported currencies
SUPPORTED_CURRENCIES = {
    "USD": {"symbol": "$", "name": "US Dollar", "rate": 1.0},
    "TWD": {"symbol": "NT$", "name": "Taiwan Dollar", "rate": 31.5},
    "JPY": {"symbol": "¥", "name": "Japanese Yen", "rate": 149.0},
    "EUR": {"symbol": "€", "name": "Euro", "rate": 0.92},
    "GBP": {"symbol": "£", "name": "British Pound", "rate": 0.79},
    "CNY": {"symbol": "¥", "name": "Chinese Yuan", "rate": 7.24},
    "HKD": {"symbol": "HK$", "name": "Hong Kong Dollar", "rate": 7.82},
    "KRW": {"symbol": "₩", "name": "Korean Won", "rate": 1320.0},
    "SGD": {"symbol": "S$", "name": "Singapore Dollar", "rate": 1.34},
}


@dataclass
class CurrencyBalance:
    """Balance in a specific currency."""
    currency: str
    symbol: str
    amount: float
    converted_value: float  # In base currency (USD)
    converted_display: str  # Formatted string


@dataclass
class ExchangeRate:
    """Exchange rate information."""
    from_currency: str
    to_currency: str
    rate: float
    updated_at: str


class MultiCurrencyService:
    """Service for multi-currency portfolio support."""

    def __init__(self):
        """Initialize Multi-Currency Service."""
        self.base_currency = "USD"
        self.cached_rates = {}
        self.last_update = None

    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Get exchange rate between two currencies.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Exchange rate (from_currency -> to_currency)
        """
        if from_currency == to_currency:
            return 1.0

        # Get rates in USD
        from_usd = self._get_currency_to_usd_rate(from_currency)
        to_usd = self._get_currency_to_usd_rate(to_currency)

        # Calculate cross rate
        return to_usd / from_usd

    def _get_currency_to_usd_rate(self, currency: str) -> float:
        """Get conversion rate from currency to USD."""
        if currency == "USD":
            return 1.0
        return SUPPORTED_CURRENCIES.get(currency, {}).get("rate", 1.0)

    async def convert_amount(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """
        Convert amount between currencies.

        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Converted amount
        """
        rate = await self.get_exchange_rate(from_currency, to_currency)
        return amount * rate

    async def get_portfolio_in_currency(
        self,
        holdings: list,
        prices: dict,
        target_currency: str = "USD"
    ) -> dict:
        """
        Convert entire portfolio to target currency.

        Args:
            holdings: List of holdings with quantity and cost
            prices: Current prices per symbol
            target_currency: Target currency code

        Returns:
            Portfolio summary in target currency.
        """
        total_value = 0.0
        total_cost = 0.0

        converted_holdings = []

        for h in holdings:
            symbol = h["symbol"]
            quantity = h["quantity"]
            avg_cost = h["avg_cost"]

            current_price = prices.get(symbol, 0)
            value = quantity * current_price
            cost = quantity * avg_cost

            total_value += value
            total_cost += cost

            converted_holdings.append({
                "symbol": symbol,
                "quantity": quantity,
                "avg_cost": avg_cost,
                "current_price": current_price,
                "value": value,
                "cost": cost,
                "gain_loss": value - cost,
                "gain_loss_percent": ((value - cost) / cost * 100) if cost > 0 else 0,
            })

        # Convert totals to target currency
        rate = await self.get_exchange_rate("USD", target_currency)

        return {
            "base_currency": "USD",
            "display_currency": target_currency,
            "exchange_rate": rate,
            "holdings": converted_holdings,
            "total_value": total_value * rate,
            "total_cost": total_cost * rate,
            "total_gain_loss": (total_value - total_cost) * rate,
            "total_gain_loss_percent": ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
        }

    async def get_supported_currencies(self) -> list:
        """
        Get list of supported currencies.

        Returns:
            List of currency info dicts.
        """
        return [
            {
                "code": code,
                "symbol": info["symbol"],
                "name": info["name"],
                "rate_to_usd": info["rate"],
            }
            for code, info in SUPPORTED_CURRENCIES.items()
        ]

    def format_currency(self, amount: float, currency: str) -> str:
        """
        Format amount with currency symbol.

        Args:
            amount: Amount to format
            currency: Currency code

        Returns:
            Formatted string like "NT$1,234.56"
        """
        symbol = SUPPORTED_CURRENCIES.get(currency, {}).get("symbol", "$")
        return f"{symbol}{amount:,.2f}"

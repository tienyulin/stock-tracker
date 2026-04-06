"""
Foreign Exchange & FX Risk Management Service
Exchange rates, currency conversion, FX hedging, natural hedge analysis
"""

import math
from datetime import datetime, timedelta
from typing import Optional
import httpx


class FXService:
    """Service for foreign exchange rate management and FX risk analysis."""

    SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CNY", "HKD", "AUD", "CAD", "TWD", "SGD", "KRW"]

    def __init__(self, db=None):
        self.db = db
        self._exchange_cache = {}
        self._last_fetch = None

    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Get exchange rate between two currencies.
        Uses free exchange rate API or falls back to cached rates.
        """
        if from_currency == to_currency:
            return 1.0

        cache_key = f"{from_currency}_{to_currency}"
        if cache_key in self._exchange_cache:
            return self._exchange_cache[cache_key]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://open.er-api.com/v6/latest/{from_currency}"
                )
                if response.status_code == 200:
                    data = response.json()
                    rates = data.get("rates", {})
                    rate = rates.get(to_currency, 1.0)
                    self._exchange_cache[cache_key] = rate
                    return rate
        except Exception:
            pass

        # Fallback to USD-based rates
        return self._get_usd_based_rate(from_currency, to_currency)

    def _get_usd_based_rate(self, from_currency: str, to_currency: str) -> float:
        """Get USD-based exchange rate (fallback)."""
        usd_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 149.50,
            "CNY": 7.24,
            "HKD": 7.82,
            "AUD": 1.53,
            "CAD": 1.36,
            "TWD": 31.50,
            "SGD": 1.34,
            "KRW": 1320.0,
        }

        from_usd = usd_rates.get(from_currency, 1.0)
        to_usd = usd_rates.get(to_currency, 1.0)
        return to_usd / from_usd

    async def convert_amount(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """Convert amount from one currency to another."""
        rate = await self.get_exchange_rate(from_currency, to_currency)
        return amount * rate

    async def get_historical_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: datetime
    ) -> float:
        """
        Get historical exchange rate (approximation using current rate with adjustment).
        In production, would use a paid historical rates API.
        """
        return await self.get_exchange_rate(from_currency, to_currency)

    def calculate_fx_sensitivity(
        self,
        positions: list,
        base_currency: str,
        volatility_pct: float = 0.05
    ) -> dict:
        """
        Calculate FX sensitivity for a portfolio.
        Returns VaR-like exposure estimate.
        """
        total_exposure = 0.0
        exposures_by_currency = {}

        for pos in positions:
            currency = pos.get("currency", "USD")
            value = pos.get("value", 0)
            value_in_base = value  # Would convert here

            exposure = value_in_base * volatility_pct
            total_exposure += exposure

            if currency not in exposures_by_currency:
                exposures_by_currency[currency] = 0
            exposures_by_currency[currency] += exposure

        return {
            "total_fx_var": round(total_exposure, 2),
            "base_currency": base_currency,
            "exposure_by_currency": {
                k: round(v, 2) for k, v in exposures_by_currency.items()
            },
            "assumed_volatility": f"{volatility_pct * 100}%"
        }

    def calculate_natural_hedge(
        self,
        assets: list,
        liabilities: list,
        base_currency: str = "USD"
    ) -> dict:
        """
        Calculate natural hedge between assets and liabilities in same currency.
        Returns hedge ratio and suggestions.
        """
        currency_positions = {}

        for asset in assets:
            currency = asset.get("currency", base_currency)
            value = asset.get("value", 0)
            if currency not in currency_positions:
                currency_positions[currency] = {"assets": 0, "liabilities": 0}
            currency_positions[currency]["assets"] += value

        for liability in liabilities:
            currency = liability.get("currency", base_currency)
            value = liability.get("value", 0)
            if currency not in currency_positions:
                currency_positions[currency] = {"assets": 0, "liabilities": 0}
            currency_positions[currency]["liabilities"] += value

        hedges = []
        total_natural_hedge = 0
        total_exposure = 0

        for currency, positions in currency_positions.items():
            assets_val = positions["assets"]
            liabilities_val = positions["liabilities"]
            net_exposure = assets_val - liabilities_val
            natural_hedge = min(assets_val, liabilities_val)

            hedge_ratio = natural_hedge / assets_val if assets_val > 0 else 0

            hedges.append({
                "currency": currency,
                "assets": round(assets_val, 2),
                "liabilities": round(liabilities_val, 2),
                "net_exposure": round(net_exposure, 2),
                "natural_hedge_amount": round(natural_hedge, 2),
                "hedge_ratio": f"{round(hedge_ratio * 100, 1)}%"
            })

            total_natural_hedge += natural_hedge
            total_exposure += assets_val

        overall_hedge_ratio = total_natural_hedge / total_exposure if total_exposure > 0 else 0

        return {
            "total_natural_hedge_amount": round(total_natural_hedge, 2),
            "total_exposure": round(total_exposure, 2),
            "overall_hedge_ratio": f"{round(overall_hedge_ratio * 100, 1)}%",
            "currency_breakdown": hedges
        }

    def calculate_hedging_cost(
        self,
        notional_amount: float,
        hedging_ratio: float,
        forward_rate: float,
        spot_rate: float,
        tenor_days: int
    ) -> dict:
        """
        Calculate cost of hedging a foreign currency exposure using forward contract.
        """
        hedged_amount = notional_amount * hedging_ratio
        forward_cost = (forward_rate - spot_rate) / spot_rate

        daily_cost_bps = (forward_cost / tenor_days) * 365 * 10000

        return {
            "notional_amount": round(notional_amount, 2),
            "hedged_amount": round(hedged_amount, 2),
            "hedging_ratio": f"{hedging_ratio * 100}%",
            "forward_rate": round(forward_rate, 4),
            "spot_rate": round(spot_rate, 4),
            "forward_cost_pct": f"{round(forward_cost * 100, 3)}%",
            "daily_cost_bps": round(daily_cost_bps, 2),
            "total_cost": round(hedged_amount * forward_cost, 2)
        }

    async def get_currency_allocation(
        self,
        positions: list,
        base_currency: str = "USD"
    ) -> dict:
        """
        Get currency allocation breakdown for a portfolio.
        """
        currency_values = {}

        for pos in positions:
            currency = pos.get("currency", base_currency)
            value = pos.get("value", 0)

            if currency not in currency_values:
                currency_values[currency] = 0
            currency_values[currency] += value

        total = sum(currency_values.values())
        allocation = []

        for currency, value in currency_values.items():
            pct = (value / total * 100) if total > 0 else 0
            allocation.append({
                "currency": currency,
                "value": round(value, 2),
                "percentage": f"{round(pct, 1)}%"
            })

        allocation.sort(key=lambda x: x["value"], reverse=True)

        return {
            "total_value": round(total, 2),
            "base_currency": base_currency,
            "allocation": allocation,
            "num_currencies": len(allocation)
        }

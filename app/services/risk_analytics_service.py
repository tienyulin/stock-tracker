"""
Risk Analytics Service

Provides portfolio risk metrics calculation including:
- Value at Risk (VaR)
- Sharpe Ratio
- Maximum Drawdown
- vs S&P 500 comparison
"""

from dataclasses import dataclass
from datetime import datetime

import math


@dataclass
class RiskMetrics:
    """Risk metrics result model."""

    portfolio_value: float
    var_95: float  # Value at Risk (95% confidence)
    var_99: float  # Value at Risk (99% confidence)
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_percent: float
    vs_sp500_return: float  # vs S&P 500 outperformance
    sp500_return: float
    portfolio_return: float
    volatility: float  # Annualized volatility
    timestamp: str


class RiskAnalyticsService:
    """Service for calculating portfolio risk metrics."""

    # Risk-free rate (approximate, could be from config)
    RISK_FREE_RATE = 0.04  # 4% annual

    def __init__(self):
        """Initialize Risk Analytics Service."""
        pass

    async def calculate_risk_metrics(
        self,
        holdings: list[dict],
        prices: dict[str, float],
        historical_prices: dict[str, list[float]],
        sp500_historical: list[float],
        risk_free_rate: float = RISK_FREE_RATE,
        trading_days: int = 252,
    ) -> RiskMetrics:
        """
        Calculate risk metrics for a portfolio.

        Args:
            holdings: List of holding dicts with 'quantity' and 'avg_cost'
            prices: Current prices dict {symbol: price}
            historical_prices: Historical closing prices {symbol: [prices]}
            sp500_historical: S&P 500 historical closing prices
            risk_free_rate: Annual risk-free rate (default 4%)
            trading_days: Trading days per year (default 252)

        Returns:
            RiskMetrics object with all calculated values.
        """
        # Calculate portfolio value
        portfolio_value = sum(
            h["quantity"] * prices.get(h["symbol"], 0)
            for h in holdings
        )

        # Calculate portfolio return
        total_cost = sum(
            h["quantity"] * h["avg_cost"]
            for h in holdings
        )
        portfolio_return = (portfolio_value - total_cost) / total_cost if total_cost > 0 else 0

        # Calculate S&P 500 return
        if len(sp500_historical) >= 2:
            sp500_current = sp500_historical[-1]
            sp500_start = sp500_historical[0]
            sp500_return = (sp500_current - sp500_start) / sp500_start if sp500_start > 0 else 0
        else:
            sp500_return = 0

        # vs S&P 500
        vs_sp500_return = portfolio_return - sp500_return

        # Calculate daily returns for all holdings
        daily_returns = self._calculate_portfolio_daily_returns(
            holdings, prices, historical_prices
        )

        # VaR calculation (historical method)
        var_95, var_99 = self._calculate_var(daily_returns)

        # Sharpe Ratio
        sharpe_ratio = self._calculate_sharpe_ratio(
            daily_returns, risk_free_rate, trading_days
        )

        # Max Drawdown
        max_drawdown, max_drawdown_percent = self._calculate_max_drawdown(daily_returns)

        # Volatility (annualized)
        volatility = self._calculate_volatility(daily_returns, trading_days)

        return RiskMetrics(
            portfolio_value=round(portfolio_value, 2),
            var_95=round(var_95, 2),
            var_99=round(var_99, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            max_drawdown=round(max_drawdown, 2),
            max_drawdown_percent=round(max_drawdown_percent, 2),
            vs_sp500_return=round(vs_sp500_return, 4),
            sp500_return=round(sp500_return, 4),
            portfolio_return=round(portfolio_return, 4),
            volatility=round(volatility, 4),
            timestamp=datetime.now().isoformat(),
        )

    def _calculate_portfolio_daily_returns(
        self,
        holdings: list[dict],
        prices: dict[str, float],
        historical_prices: dict[str, list[float]],
    ) -> list[float]:
        """
        Calculate weighted portfolio daily returns.

        Returns list of daily portfolio returns.
        """
        # Find minimum history length
        min_len = float('inf')
        for h in holdings:
            symbol = h["symbol"]
            if symbol in historical_prices and len(historical_prices[symbol]) >= 2:
                min_len = min(min_len, len(historical_prices[symbol]))

        if min_len == float('inf') or min_len < 2:
            return [0.0]

        # Calculate portfolio weights
        total_value = sum(
            h["quantity"] * prices.get(h["symbol"], 0)
            for h in holdings
        )

        if total_value == 0:
            return [0.0]

        # Calculate weighted daily returns
        daily_returns = []
        for day_idx in range(1, min_len):
            daily_return = 0.0
            for h in holdings:
                symbol = h["symbol"]
                if symbol not in historical_prices:
                    continue
                prices_list = historical_prices[symbol]
                if len(prices_list) <= day_idx:
                    continue

                current_price = prices_list[day_idx]
                prev_price = prices_list[day_idx - 1]
                if prev_price == 0:
                    continue

                holding_value = h["quantity"] * current_price
                weight = holding_value / total_value
                daily_return += weight * ((current_price - prev_price) / prev_price)

            daily_returns.append(daily_return)

        return daily_returns if daily_returns else [0.0]

    def _calculate_var(self, daily_returns: list[float]) -> tuple[float, float]:
        """
        Calculate Value at Risk using historical method.

        Args:
            daily_returns: List of daily returns.

        Returns:
            Tuple of (VaR 95%, VaR 99%).
        """
        if not daily_returns:
            return 0.0, 0.0

        sorted_returns = sorted(daily_returns)
        n = len(sorted_returns)

        # VaR 95% (5th percentile)
        idx_95 = int(n * 0.05)
        var_95 = sorted_returns[max(0, idx_95 - 1)]

        # VaR 99% (1st percentile)
        idx_99 = int(n * 0.01)
        var_99 = sorted_returns[max(0, idx_99 - 1)]

        return abs(var_95), abs(var_99)

    def _calculate_sharpe_ratio(
        self,
        daily_returns: list[float],
        risk_free_rate: float,
        trading_days: int,
    ) -> float:
        """
        Calculate Sharpe Ratio.

        Args:
            daily_returns: List of daily returns.
            risk_free_rate: Annual risk-free rate.
            trading_days: Trading days per year.

        Returns:
            Sharpe Ratio.
        """
        if not daily_returns or len(daily_returns) < 2:
            return 0.0

        # Daily risk-free rate
        daily_rf = risk_free_rate / trading_days

        # Excess returns
        excess_returns = [r - daily_rf for r in daily_returns]

        # Mean excess return
        mean_excess = sum(excess_returns) / len(excess_returns)

        # Standard deviation
        variance = sum((r - mean_excess) ** 2 for r in excess_returns) / (len(excess_returns) - 1)
        std_dev = math.sqrt(variance) if variance > 0 else 0

        if std_dev == 0:
            return 0.0

        # Annualized Sharpe Ratio
        sharpe = (mean_excess / std_dev) * math.sqrt(trading_days)

        return sharpe

    def _calculate_max_drawdown(
        self, daily_returns: list[float]
    ) -> tuple[float, float]:
        """
        Calculate Maximum Drawdown.

        Args:
            daily_returns: List of daily returns.

        Returns:
            Tuple of (max drawdown in $, max drawdown percent).
        """
        if not daily_returns:
            return 0.0, 0.0

        cumulative = 1.0
        running_max = 1.0
        max_dd = 0.0
        max_dd_percent = 0.0

        for r in daily_returns:
            cumulative *= (1 + r)
            running_max = max(running_max, cumulative)
            drawdown = running_max - cumulative
            drawdown_percent = drawdown / running_max if running_max > 0 else 0

            if drawdown > max_dd:
                max_dd = drawdown
            if drawdown_percent > max_dd_percent:
                max_dd_percent = drawdown_percent

        return max_dd, max_dd_percent

    def _calculate_volatility(
        self, daily_returns: list[float], trading_days: int
    ) -> float:
        """
        Calculate annualized volatility.

        Args:
            daily_returns: List of daily returns.
            trading_days: Trading days per year.

        Returns:
            Annualized volatility.
        """
        if not daily_returns or len(daily_returns) < 2:
            return 0.0

        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        daily_vol = math.sqrt(variance)

        # Annualize
        return daily_vol * math.sqrt(trading_days)

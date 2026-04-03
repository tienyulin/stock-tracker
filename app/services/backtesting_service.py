"""
Portfolio Backtesting Service

Backtests trading strategies against historical data to evaluate performance.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import math


@dataclass
class BacktestTrade:
    """Simulated trade during backtest."""
    date: str
    action: str  # BUY, SELL
    symbol: str
    quantity: float
    price: float
    value: float


@dataclass
class BacktestMetrics:
    """Backtest performance metrics."""
    total_return: float
    total_return_percent: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_percent: float
    volatility: float
    win_rate: float  # Percentage of profitable trades
    trade_count: int
    benchmark_return: float  # S&P 500 return over same period
    alpha: float  # Excess return vs benchmark
    timestamp: str


@dataclass
class BacktestResult:
    """Complete backtest result."""
    symbol: str
    strategy: str
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    metrics: BacktestMetrics
    trades: list[BacktestTrade]
    equity_curve: list[dict]  # {date, value}


class PortfolioBacktestingService:
    """Service for backtesting portfolio strategies."""

    # Default trading parameters
    DEFAULT_SHORT_MA = 20
    DEFAULT_LONG_MA = 50
    DEFAULT_INITIAL_CAPITAL = 10000.0

    def __init__(self):
        """Initialize Backtesting Service."""
        pass

    async def run_backtest(
        self,
        symbol: str,
        historical_prices: list[float],
        dates: list[str],
        strategy: str = "sma_crossover",
        short_period: int = DEFAULT_SHORT_MA,
        long_period: int = DEFAULT_LONG_MA,
        initial_capital: float = DEFAULT_INITIAL_CAPITAL,
    ) -> BacktestResult:
        """
        Run backtest for a given strategy.

        Args:
            symbol: Stock symbol to backtest
            historical_prices: List of historical closing prices
            dates: List of date strings corresponding to prices
            strategy: Strategy name (default 'sma_crossover')
            short_period: Short MA period
            long_period: Long MA period
            initial_capital: Starting capital

        Returns:
            BacktestResult with metrics and trade history.
        """
        if len(historical_prices) < long_period:
            raise ValueError(f"Insufficient data: need at least {long_period} periods")

        if strategy == "sma_crossover":
            return await self._sma_crossover_backtest(
                symbol, historical_prices, dates,
                short_period, long_period, initial_capital
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    async def _sma_crossover_backtest(
        self,
        symbol: str,
        prices: list[float],
        dates: list[str],
        short_period: int,
        long_period: int,
        initial_capital: float,
    ) -> BacktestResult:
        """Simple Moving Average Crossover strategy backtest."""

        cash = initial_capital
        shares = 0.0
        position_open = False

        trades = []
        equity_curve = []

        # Calculate SMAs
        short_ma_values = self._calculate_sma(prices, short_period)
        long_ma_values = self._calculate_sma(prices, long_period)

        # Align prices with MA values (starting from long_period)
        start_idx = long_period
        price_offset = len(prices) - len(long_ma_values)

        for i in range(start_idx, len(prices)):
            price = prices[i]
            date = dates[i] if i < len(dates) else f"Day_{i}"

            short_ma = short_ma_values[i - price_offset]
            long_ma = long_ma_values[i - price_offset]

            current_value = cash + shares * price

            # Record equity curve
            equity_curve.append({
                "date": date,
                "value": round(current_value, 2)
            })

            # Trading signals
            if short_ma > long_ma and not position_open:
                # BUY signal
                shares = cash / price
                cash = 0
                position_open = True
                trades.append(BacktestTrade(
                    date=date,
                    action="BUY",
                    symbol=symbol,
                    quantity=shares,
                    price=price,
                    value=round(shares * price, 2)
                ))

            elif short_ma < long_ma and position_open:
                # SELL signal
                cash = shares * price
                trades.append(BacktestTrade(
                    date=date,
                    action="SELL",
                    symbol=symbol,
                    quantity=shares,
                    price=price,
                    value=round(cash, 2)
                ))
                shares = 0.0
                position_open = False

        # Calculate final metrics
        final_value = cash + shares * prices[-1]
        total_return = final_value - initial_capital
        total_return_percent = (total_return / initial_capital) * 100

        # Calculate daily returns from equity curve
        daily_returns = []
        for j in range(1, len(equity_curve)):
            prev_value = equity_curve[j-1]["value"]
            curr_value = equity_curve[j]["value"]
            if prev_value > 0:
                daily_returns.append((curr_value - prev_value) / prev_value)

        # Calculate metrics
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        max_dd, max_dd_pct = self._calculate_max_drawdown(daily_returns)
        volatility = self._calculate_volatility(daily_returns)

        # Win rate
        winning_trades = 0
        for j in range(1, len(trades), 2):  # Every SELL after BUY
            if j < len(trades):
                sell_value = trades[j].value
                buy_value = trades[j-1].value if j > 0 else 0
                if sell_value > buy_value:
                    winning_trades += 1

        total_closed_trades = len([t for t in trades if t.action == "SELL"])
        win_rate = winning_trades / total_closed_trades if total_closed_trades > 0 else 0

        # Benchmark return (assume S&P 500 grew 10% annually as proxy)
        days = len(dates) if dates else 252
        years = days / 252
        benchmark_return = initial_capital * (1.10 ** years) - initial_capital
        benchmark_return_percent = ((1.10 ** years) - 1) * 100
        alpha = total_return - benchmark_return

        metrics = BacktestMetrics(
            total_return=round(total_return, 2),
            total_return_percent=round(total_return_percent, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            max_drawdown=round(max_dd, 2),
            max_drawdown_percent=round(max_dd_pct, 2),
            volatility=round(volatility, 2),
            win_rate=round(win_rate, 4),
            trade_count=len(trades),
            benchmark_return=round(benchmark_return_percent, 2),
            alpha=round(alpha, 2),
            timestamp=datetime.now().isoformat(),
        )

        return BacktestResult(
            symbol=symbol,
            strategy="sma_crossover",
            start_date=dates[0] if dates else "",
            end_date=dates[-1] if dates else "",
            initial_capital=initial_capital,
            final_value=round(final_value, 2),
            metrics=metrics,
            trades=trades,
            equity_curve=equity_curve,
        )

    def _calculate_sma(self, prices: list[float], period: int) -> list[float]:
        """Calculate Simple Moving Average."""
        sma_values = []
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1:i + 1]
            sma = sum(window) / period
            sma_values.append(sma)
        return sma_values

    def _calculate_sharpe_ratio(self, daily_returns: list[float]) -> float:
        """Calculate Sharpe Ratio."""
        if not daily_returns or len(daily_returns) < 2:
            return 0.0

        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        std_dev = math.sqrt(variance) if variance > 0 else 0

        if std_dev == 0:
            return 0.0

        # Annualized Sharpe Ratio (252 trading days)
        sharpe = (mean_return / std_dev) * math.sqrt(252)
        return sharpe

    def _calculate_max_drawdown(self, daily_returns: list[float]) -> tuple[float, float]:
        """Calculate Maximum Drawdown."""
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

    def _calculate_volatility(self, daily_returns: list[float]) -> float:
        """Calculate annualized volatility."""
        if not daily_returns or len(daily_returns) < 2:
            return 0.0

        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        daily_vol = math.sqrt(variance)

        # Annualize
        return daily_vol * math.sqrt(252)

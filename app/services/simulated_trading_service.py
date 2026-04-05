"""
Simulated Trading Service

Provides paper trading simulation based on signals.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid

from app.services.signal_engine_service import SignalEngineService, SignalType


class RiskProfile(Enum):
    """Risk profile types."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class Position:
    """Represents a stock position."""
    symbol: str
    shares: float
    avg_price: float
    buy_date: datetime


@dataclass
class Trade:
    """Represents a trade execution."""
    id: str
    timestamp: datetime
    symbol: str
    action: str  # "BUY" or "SELL"
    shares: float
    price: float
    total: float
    reason: str


@dataclass
class SimulationResult:
    """Simulation result summary."""
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percent: float
    num_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    trades: list[Trade]


@dataclass
class SimulationConfig:
    """Simulation configuration."""
    initial_capital: float = 5000.0
    duration_days: int = 30
    risk_profile: RiskProfile = RiskProfile.MODERATE
    max_position_percent: float = 0.20  # 20% of capital per trade

    # Risk profile settings
    CONSERVATIVE_MIN_CONFIDENCE = 80.0
    CONSERVATIVE_MAX_POSITION = 0.10
    MODERATE_MIN_CONFIDENCE = 60.0
    MODERATE_MAX_POSITION = 0.20
    AGGRESSIVE_MIN_CONFIDENCE = 40.0
    AGGRESSIVE_MAX_POSITION = 0.50

    def get_min_confidence(self) -> float:
        if self.risk_profile == RiskProfile.CONSERVATIVE:
            return self.CONSERVATIVE_MIN_CONFIDENCE
        elif self.risk_profile == RiskProfile.MODERATE:
            return self.MODERATE_MIN_CONFIDENCE
        else:
            return self.AGGRESSIVE_MIN_CONFIDENCE

    def get_max_position_percent(self) -> float:
        if self.risk_profile == RiskProfile.CONSERVATIVE:
            return self.CONSERVATIVE_MAX_POSITION
        elif self.risk_profile == RiskProfile.MODERATE:
            return self.MODERATE_MAX_POSITION
        else:
            return self.AGGRESSIVE_MAX_POSITION


class SimulatedTradingService:
    """
    Service for simulating stock trades based on signals.

    Uses Signal Engine to generate buy/sell decisions and tracks
    simulated portfolio performance.
    """

    def __init__(self):
        """Initialize the trading service."""
        self._signal_engine = SignalEngineService()

    async def run_simulation(
        self,
        symbols: list[str],
        config: SimulationConfig,
    ) -> SimulationResult:
        """
        Run a trading simulation.

        Args:
            symbols: List of stock symbols to consider
            config: Simulation configuration

        Returns:
            SimulationResult with trading history and performance
        """
        capital = config.initial_capital
        positions: dict[str, Position] = {}
        trades: list[Trade] = []
        cash = capital

        min_confidence = config.get_min_confidence()
        max_position_pct = config.get_max_position_percent()

        # For each symbol, get signal and decide
        for symbol in symbols:
            try:
                signal = await self._signal_engine.get_signal(symbol)
                if not signal:
                    continue

                # Check if we should buy
                should_buy = (
                    signal.overall_signal in (SignalType.STRONG_BUY, SignalType.BUY)
                    and signal.confidence >= min_confidence
                )

                # Check if we should sell existing position
                should_sell = (
                    signal.overall_signal in (SignalType.STRONG_SELL, SignalType.SELL)
                    and symbol in positions
                )

                # Calculate position size
                max_investment = cash * max_position_pct
                if max_investment < 100:  # Minimum $100 per trade
                    continue

                # Execute buy
                if should_buy and symbol not in positions:
                    # Get current price (simplified - use latest close)
                    # In real implementation, would fetch actual price
                    current_price = 100.0  # Placeholder
                    shares_to_buy = min(max_investment / current_price, 100)

                    if shares_to_buy >= 1:
                        trade = Trade(
                            id=str(uuid.uuid4()),
                            timestamp=datetime.now(),
                            symbol=symbol,
                            action="BUY",
                            shares=shares_to_buy,
                            price=current_price,
                            total=shares_to_buy * current_price,
                            reason=f"Signal: {signal.signal_label} ({signal.confidence}%)",
                        )
                        trades.append(trade)
                        positions[symbol] = Position(
                            symbol=symbol,
                            shares=shares_to_buy,
                            avg_price=current_price,
                            buy_date=datetime.now(),
                        )
                        cash -= trade.total

                # Execute sell
                elif should_sell and symbol in positions:
                    position = positions[symbol]
                    current_price = 100.0  # Placeholder

                    trade = Trade(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        symbol=symbol,
                        action="SELL",
                        shares=position.shares,
                        price=current_price,
                        total=position.shares * current_price,
                        reason=f"Signal: {signal.signal_label} ({signal.confidence}%)",
                    )
                    trades.append(trade)
                    cash += trade.total
                    del positions[symbol]

            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue

        # Close all positions at end
        for symbol, position in list(positions.items()):
            # Simplified - would get actual final price
            final_price = position.avg_price * 1.05  # Assume 5% gain
            trade = Trade(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                symbol=symbol,
                action="SELL",
                shares=position.shares,
                price=final_price,
                total=position.shares * final_price,
                reason="Simulation ended",
            )
            trades.append(trade)
            cash += trade.total
            del positions[symbol]

        # Calculate results
        final_capital = cash
        total_return = final_capital - config.initial_capital
        total_return_pct = (total_return / config.initial_capital) * 100 if config.initial_capital > 0 else 0

        winning_trades = sum(1 for t in trades if t.action == "SELL" and t.total > 0)
        losing_trades = sum(1 for t in trades if t.action == "SELL" and t.total <= 0)
        num_trades = len([t for t in trades if t.action in ("BUY", "SELL")])
        win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0

        return SimulationResult(
            initial_capital=config.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_percent=total_return_pct,
            num_trades=num_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            trades=trades,
        )

    async def quick_evaluate(
        self,
        symbol: str,
        config: SimulationConfig,
    ) -> dict:
        """
        Quick evaluation of a single symbol for simulation.

        Args:
            symbol: Stock symbol
            config: Simulation configuration

        Returns:
            Dict with evaluation result
        """
        signal = await self._signal_engine.get_signal(symbol)
        if not signal:
            return {"symbol": symbol, "should_buy": False, "reason": "No signal data"}

        min_confidence = config.get_min_confidence()
        max_position_pct = config.get_max_position_percent()

        should_buy = (
            signal.overall_signal in (SignalType.STRONG_BUY, SignalType.BUY)
            and signal.confidence >= min_confidence
        )

        return {
            "symbol": symbol,
            "should_buy": should_buy,
            "signal": signal.signal_label,
            "confidence": signal.confidence,
            "reason": f"Confidence {signal.confidence}% vs required {min_confidence}%",
            "max_position_percent": max_position_pct * 100,
            "bullish_factors": signal.bullish_factors[:2],
            "bearish_factors": signal.bearish_factors[:2],
        }

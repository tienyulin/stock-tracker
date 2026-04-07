"""
Copy Trading & Social Trading Service
Follow traders, auto-sync trades, performance tracking, paper trading
"""

import math
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import httpx


class CopyTradingService:
    """Service for copy trading and social trading features."""

    def __init__(self, db=None):
        self.db = db
        self._cache = {}

    def calculate_performance(
        self,
        initial_value: float,
        current_value: float,
        time_period_days: int = 365
    ) -> dict:
        """Calculate trading performance metrics."""
        total_return = ((current_value - initial_value) / initial_value * 100) if initial_value > 0 else 0
        annualized_return = (total_return / time_period_days * 365) if time_period_days > 0 else 0

        return {
            "initial_value": initial_value,
            "current_value": current_value,
            "total_return_pct": round(total_return, 2),
            "annualized_return_pct": round(annualized_return, 2),
            "absolute_return": round(current_value - initial_value, 2),
            "time_period_days": time_period_days
        }

    def get_trader_score(
        self,
        win_rate: float,
        sharpe_ratio: float,
        max_drawdown: float,
        followers_count: int
    ) -> dict:
        """
        Calculate overall trader score (0-100).
        Based on performance, consistency, and popularity.
        """
        performance_score = min(win_rate * 40, 40)  # Up to 40 points
        risk_adjusted_score = min(sharpe_ratio * 20, 20)  # Up to 20 points
        drawdown_score = max(0, (20 + max_drawdown * 20))  # Up to 20 points (lower drawdown = better)
        popularity_score = min(math.log10(followers_count + 1) * 10, 20)  # Up to 20 points

        total_score = performance_score + risk_adjusted_score + drawdown_score + popularity_score

        return {
            "total_score": round(min(total_score, 100), 1),
            "performance_score": round(performance_score, 1),
            "risk_adjusted_score": round(risk_adjusted_score, 1),
            "drawdown_score": round(drawdown_score, 1),
            "popularity_score": round(popularity_score, 1),
            "rating": self._get_rating(total_score)
        }

    def _get_rating(self, score: float) -> str:
        """Get trader rating based on score."""
        if score >= 90:
            return "⭐ Elite"
        elif score >= 75:
            return "🌟 Expert"
        elif score >= 60:
            return "📈 Advanced"
        elif score >= 40:
            return "📊 Intermediate"
        else:
            return "📉 Beginner"

    def calculate_copy_allocation(
        self,
        follower_capital: float,
        trader_allocation_pct: float,
        max_copy_pct: float = 20
    ) -> dict:
        """
        Calculate how much capital to allocate when copying a trader.
        """
        allocation_pct = min(trader_allocation_pct, max_copy_pct)
        allocated_amount = follower_capital * (allocation_pct / 100)

        return {
            "follower_capital": follower_capital,
            "allocation_percentage": allocation_pct,
            "allocated_amount": round(allocated_amount, 2),
            "remaining_capital": round(follower_capital - allocated_amount, 2),
            "max_copy_limit_reached": trader_allocation_pct > max_copy_pct
        }

    def sync_trade(
        self,
        original_trade_value: float,
        copy_ratio: float,
        follower_capital: float
    ) -> dict:
        """
        Calculate synchronized trade for follower based on copy ratio.
        """
        synced_value = original_trade_value * copy_ratio

        # Ensure doesn't exceed follower's available capital
        max_synced_value = follower_capital * 0.2  # Max 20% per trade
        actual_synced = min(synced_value, max_synced_value)
        actual_ratio = actual_synced / original_trade_value if original_trade_value > 0 else 0

        return {
            "original_trade_value": original_trade_value,
            "planned_copy_ratio": copy_ratio,
            "planned_synced_value": round(synced_value, 2),
            "actual_synced_value": round(actual_synced, 2),
            "actual_copy_ratio": round(actual_ratio, 4),
            "capital_utilization_pct": round(actual_synced / follower_capital * 100, 2) if follower_capital > 0 else 0
        }

    def calculate_risk_score(
        self,
        positions: list,
        total_capital: float,
        concentration_limit: float = 0.3
    ) -> dict:
        """
        Calculate copy trading risk score for a trader.
        """
        if not positions or total_capital == 0:
            return {"risk_score": 0, "risk_level": "Unknown"}

        # Position concentration risk
        largest_position = max(positions, key=lambda x: x.get("value", 0))
        largest_pct = (largest_position.get("value", 0) / total_capital * 100) if total_capital > 0 else 0
        concentration_risk = "High" if largest_pct > concentration_limit * 100 else "Normal"

        # Count positions
        num_positions = len(positions)

        # Overall risk score
        risk_score = 50  # Base
        if concentration_risk == "High":
            risk_score += 25
        if num_positions < 3:
            risk_score += 15
        if num_positions > 20:
            risk_score -= 10

        return {
            "risk_score": min(risk_score, 100),
            "risk_level": "High" if risk_score > 70 else ("Medium" if risk_score > 40 else "Low"),
            "largest_position_pct": round(largest_pct, 1),
            "num_positions": num_positions,
            "concentration_risk": concentration_risk
        }

    def get_leaderboard(
        self,
        traders: list,
        sort_by: str = "score",
        limit: int = 20
    ) -> list:
        """
        Get copy trading leaderboard sorted by performance.
        """
        sorted_traders = traders

        if sort_by == "return":
            sorted_traders = sorted(traders, key=lambda x: x.get("annualized_return", 0), reverse=True)
        elif sort_by == "followers":
            sorted_traders = sorted(traders, key=lambda x: x.get("followers_count", 0), reverse=True)
        elif sort_by == "win_rate":
            sorted_traders = sorted(traders, key=lambda x: x.get("win_rate", 0), reverse=True)
        else:  # score
            sorted_traders = sorted(traders, key=lambda x: x.get("score", 0), reverse=True)

        return sorted_traders[:limit]

    def generate_copy_warning(
        self,
        trader_drawdown: float,
        trader_max_drawdown: float,
        follower_allocation_pct: float
    ) -> list:
        """
        Generate risk warnings for copying a trader.
        """
        warnings = []

        if trader_drawdown > trader_max_drawdown * 0.8:
            warnings.append({
                "level": "high",
                "message": "Trader approaching max drawdown limit"
            })

        if follower_allocation_pct > 20:
            warnings.append({
                "level": "medium",
                "message": "High allocation to single trader (>20%)"
            })

        return warnings


class PaperTradingService:
    """Service for paper trading (simulated trading with virtual money)."""

    PAPER_INITIAL_CAPITAL = 1_000_000  # 1M virtual currency

    def __init__(self, db=None):
        self.db = db

    def create_paper_account(self, user_id: str) -> dict:
        """Create a new paper trading account."""
        return {
            "user_id": user_id,
            "cash_balance": self.PAPER_INITIAL_CAPITAL,
            "initial_capital": self.PAPER_INITIAL_CAPITAL,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }

    def execute_paper_trade(
        self,
        symbol: str,
        quantity: int,
        price: float,
        trade_type: str,  # BUY or SELL
        current_cash: float,
        current_positions: dict
    ) -> dict:
        """
        Execute a paper trade and return updated portfolio state.
        """
        if trade_type == "BUY":
            cost = price * quantity
            if cost > current_cash:
                return {"success": False, "error": "Insufficient cash"}
            new_cash = current_cash - cost
            new_position = current_positions.get(symbol, 0) + quantity
        else:  # SELL
            if current_positions.get(symbol, 0) < quantity:
                return {"success": False, "error": "Insufficient shares"}
            proceeds = price * quantity
            new_cash = current_cash + proceeds
            new_position = current_positions.get(symbol, 0) - quantity

        return {
            "success": True,
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "trade_type": trade_type,
            "new_cash_balance": round(new_cash, 2),
            "new_position": new_position,
            "timestamp": datetime.now().isoformat()
        }

    def calculate_paper_performance(
        self,
        initial_capital: float,
        current_cash: float,
        positions: dict,
        current_prices: dict
    ) -> dict:
        """
        Calculate paper trading performance vs real portfolio.
        """
        position_value = sum(
            current_prices.get(symbol, 0) * qty
            for symbol, qty in positions.items()
        )
        total_value = current_cash + position_value
        absolute_return = total_value - initial_capital
        return_pct = (absolute_return / initial_capital * 100) if initial_capital > 0 else 0

        return {
            "initial_capital": initial_capital,
            "current_cash": round(current_cash, 2),
            "positions_value": round(position_value, 2),
            "total_value": round(total_value, 2),
            "absolute_return": round(absolute_return, 2),
            "return_pct": round(return_pct, 2),
            "status": "Profit" if absolute_return > 0 else "Loss"
        }

    def compare_vs_real(
        self,
        paper_return_pct: float,
        real_return_pct: float
    ) -> dict:
        """
        Compare paper trading performance to real portfolio.
        """
        outperformance = paper_return_pct - real_return_pct

        return {
            "paper_return_pct": paper_return_pct,
            "real_return_pct": real_return_pct,
            "outperformance_pct": round(outperformance, 2),
            "verdict": "Paper beating real" if outperformance > 0 else "Real beating paper"
        }

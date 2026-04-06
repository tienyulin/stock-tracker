"""Models package."""
from app.models.models import Alert, AlertNotification, Base, User, UserHolding, Watchlist, WatchlistItem
from app.models.social import Follow, LeaderboardEntry, TradeActivity, UserProfile
from app.models.portfolio_health import HealthScoreAlert, PortfolioHealthScore
from app.models.options import OptionContract, OptionPosition
from app.models.dividend import DividendPayment, DividendHolding, ExDividendCalendar
from app.models.passive_income import (
    FireGoal,
    PassiveIncomeRecord,
    PassiveIncomeSource,
)
from app.models.fixed_income import Bond, TermDeposit
from app.models.commodities import CommodityPosition, FuturesContract

__all__ = [
    "Alert",
    "AlertNotification",
    "Base",
    "Bond",
    "CommodityPosition",
    "DividendHolding",
    "DividendPayment",
    "ExDividendCalendar",
    "FireGoal",
    "Follow",
    "FuturesContract",
    "HealthScoreAlert",
    "LeaderboardEntry",
    "OptionContract",
    "OptionPosition",
    "PassiveIncomeRecord",
    "PassiveIncomeSource",
    "PortfolioHealthScore",
    "TermDeposit",
    "TradeActivity",
    "User",
    "UserHolding",
    "UserProfile",
    "Watchlist",
    "WatchlistItem",
]


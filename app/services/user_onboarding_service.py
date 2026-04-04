"""
User Onboarding Service - Phase 17

Provides user onboarding experience improvements:
- Interactive onboarding tour
- Sample portfolio setup
- Quick-start templates
- Suggested allocations
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class OnboardingStepType(Enum):
    """Onboarding step types."""

    WELCOME = "welcome"
    PROFILE_SETUP = "profile_setup"
    FIRST_WATCHLIST = "first_watchlist"
    FIRST_ALERT = "first_alert"
    FIRST_PORTFOLIO = "first_portfolio"


class RiskLevel(Enum):
    """Risk level for portfolio templates."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class OnboardingStep:
    """Onboarding step data model."""

    step_type: OnboardingStepType
    title: str
    description: str
    is_completed: bool = False
    order: int = 0
    completed_at: Optional[datetime] = None


@dataclass
class Allocation:
    """Asset allocation for a portfolio template."""

    category: str  # e.g., "stocks", "bonds", "cash", "etfs"
    percentage: int  # 0-100
    description: str = ""


@dataclass
class PortfolioTemplate:
    """Portfolio template for quick-start."""

    name: str
    description: str
    risk_level: str  # LOW, MEDIUM, HIGH
    allocations: list[Allocation]
    suggested_stocks: list[str] = field(default_factory=list)


@dataclass
class FirstPortfolio:
    """First portfolio created during onboarding."""

    id: str
    user_id: str
    template_name: str
    initial_capital: float
    holdings: list[dict]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OnboardingProgress:
    """User onboarding progress."""

    user_id: str
    completed_steps: int
    total_steps: int
    percentage: int
    is_complete: bool
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class UserOnboardingService:
    """Service for managing user onboarding experience."""

    TOTAL_STEPS = 5

    def __init__(self):
        """Initialize User Onboarding Service."""
        self._user_progress: dict[str, dict[OnboardingStepType, datetime]] = {}
        self._completed_onboarding: set[str] = set()
        self._first_portfolios: dict[str, FirstPortfolio] = {}

    def get_onboarding_steps(self, user_id: str) -> list[OnboardingStep]:
        """
        Get all onboarding steps for a user.

        Args:
            user_id: User identifier

        Returns:
            List of onboarding steps with completion status
        """
        steps_data = [
            (OnboardingStepType.WELCOME, "Welcome to Stock Tracker", "Let's get you started with your investment journey", 1),
            (OnboardingStepType.PROFILE_SETUP, "Set Up Your Profile", "Tell us about your investment goals", 2),
            (OnboardingStepType.FIRST_WATCHLIST, "Create Your First Watchlist", "Track stocks you're interested in", 3),
            (OnboardingStepType.FIRST_ALERT, "Set Your First Alert", "Get notified when stocks hit your target prices", 4),
            (OnboardingStepType.FIRST_PORTFOLIO, "Create Your Portfolio", "Build your first investment portfolio", 5),
        ]

        completed_steps = self._user_progress.get(user_id, {})

        steps = []
        for step_type, title, description, order in steps_data:
            step = OnboardingStep(
                step_type=step_type,
                title=title,
                description=description,
                is_completed=step_type in completed_steps,
                order=order,
                completed_at=completed_steps.get(step_type),
            )
            steps.append(step)

        return steps

    def complete_step(self, user_id: str, step_type: OnboardingStepType | str) -> bool:
        """
        Mark an onboarding step as completed.

        Args:
            user_id: User identifier
            step_type: Step type to complete

        Returns:
            True if step was completed successfully
        """
        if isinstance(step_type, str):
            try:
                step_type = OnboardingStepType(step_type)
            except ValueError:
                return False

        if step_type not in OnboardingStepType:
            return False

        if user_id not in self._user_progress:
            self._user_progress[user_id] = {}

        self._user_progress[user_id][step_type] = datetime.utcnow()
        return True

    def get_progress(self, user_id: str) -> OnboardingProgress:
        """
        Get onboarding progress for a user.

        Args:
            user_id: User identifier

        Returns:
            Onboarding progress data
        """
        completed_steps = len(self._user_progress.get(user_id, {}))
        total_steps = self.TOTAL_STEPS
        percentage = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
        is_complete = self.is_onboarding_complete(user_id)

        started_at = datetime.utcnow()
        completed_at = None

        if user_id in self._completed_onboarding:
            completed_at = datetime.utcnow()

        return OnboardingProgress(
            user_id=user_id,
            completed_steps=completed_steps,
            total_steps=total_steps,
            percentage=percentage,
            is_complete=is_complete,
            started_at=started_at,
            completed_at=completed_at,
        )

    def is_onboarding_complete(self, user_id: str) -> bool:
        """
        Check if user has completed onboarding.

        Args:
            user_id: User identifier

        Returns:
            True if onboarding is complete
        """
        if user_id in self._completed_onboarding:
            return True

        completed = len(self._user_progress.get(user_id, {}))
        return completed >= self.TOTAL_STEPS

    def mark_onboarding_complete(self, user_id: str) -> None:
        """Mark onboarding as complete for a user."""
        self._completed_onboarding.add(user_id)

    def get_portfolio_templates(self) -> list[PortfolioTemplate]:
        """
        Get available portfolio templates for quick-start.

        Returns:
            List of portfolio templates
        """
        templates = [
            PortfolioTemplate(
                name="Conservative",
                description="Low risk, stable returns. Ideal for beginners or those who prefer safety.",
                risk_level="LOW",
                allocations=[
                    Allocation(category="bonds", percentage=50, description="50% Government & Corporate Bonds"),
                    Allocation(category="etfs", percentage=30, description="30% Index ETFs (S&P 500)"),
                    Allocation(category="cash", percentage=20, description="20% Cash & Money Market"),
                ],
                suggested_stocks=["SPY", "BND", "VTI"],
            ),
            PortfolioTemplate(
                name="Balanced",
                description="Mix of growth and stability. Suitable for most investors.",
                risk_level="MEDIUM",
                allocations=[
                    Allocation(category="stocks", percentage=60, description="60% Individual Stocks & ETFs"),
                    Allocation(category="bonds", percentage=30, description="30% Bonds"),
                    Allocation(category="cash", percentage=10, description="10% Cash Reserve"),
                ],
                suggested_stocks=["AAPL", "GOOGL", "MSFT", "BND", "VTI"],
            ),
            PortfolioTemplate(
                name="Aggressive",
                description="High growth potential. For experienced investors comfortable with volatility.",
                risk_level="HIGH",
                allocations=[
                    Allocation(category="stocks", percentage=80, description="80% Growth Stocks"),
                    Allocation(category="crypto", percentage=10, description="10% Cryptocurrency (optional)"),
                    Allocation(category="cash", percentage=10, description="10% Cash for Opportunities"),
                ],
                suggested_stocks=["NVDA", "TSLA", "AAPL", "AMD", "COIN"],
            ),
        ]

        return templates

    def create_first_portfolio(
        self,
        user_id: str,
        template_name: str,
        initial_capital: float = 10000.0,
        custom_allocations: Optional[list[dict]] = None,
    ) -> FirstPortfolio:
        """
        Create a first portfolio based on a template.

        Args:
            user_id: User identifier
            template_name: Name of portfolio template to use
            initial_capital: Starting capital amount
            custom_allocations: Optional custom allocations

        Returns:
            Created first portfolio
        """
        templates = {t.name.lower(): t for t in self.get_portfolio_templates()}
        template = templates.get(template_name.lower())

        if not template:
            # Default to balanced if template not found
            template = templates.get("balanced")

        holdings = []

        if custom_allocations:
            for alloc in custom_allocations:
                symbol = alloc.get("symbol", "")
                percentage = alloc.get("percentage", 0)
                if symbol and percentage > 0:
                    holdings.append({
                        "symbol": symbol,
                        "allocation_percentage": percentage,
                        "dollar_amount": initial_capital * (percentage / 100),
                        "shares": 0,  # Would be calculated based on current price
                    })
        else:
            # Use template allocations
            for alloc in template.allocations:
                if alloc.percentage > 0:
                    # Find a suggested stock for this category
                    symbol = self._get_symbol_for_category(alloc.category, template.suggested_stocks)
                    if symbol:
                        holdings.append({
                            "symbol": symbol,
                            "category": alloc.category,
                            "allocation_percentage": alloc.percentage,
                            "dollar_amount": initial_capital * (alloc.percentage / 100),
                            "shares": 0,
                        })

        portfolio = FirstPortfolio(
            id=str(uuid.uuid4()),
            user_id=user_id,
            template_name=template.name,
            initial_capital=initial_capital,
            holdings=holdings,
        )

        self._first_portfolios[user_id] = portfolio

        # Mark onboarding complete
        self.mark_onboarding_complete(user_id)

        return portfolio

    def _get_symbol_for_category(self, category: str, suggested_stocks: list[str]) -> Optional[str]:
        """Get a stock symbol for a given category."""
        # Simple mapping for demo purposes
        category_map = {
            "stocks": suggested_stocks[0] if suggested_stocks else "AAPL",
            "etfs": "SPY",
            "bonds": "BND",
            "crypto": "BTC",
            "cash": None,
        }
        return category_map.get(category)

    def get_suggested_watchlists(self) -> list[dict]:
        """
        Get suggested watchlists for new users.

        Returns:
            List of suggested watchlists
        """
        return [
            {
                "name": "Tech Giants",
                "description": "Major technology companies",
                "symbols": ["AAPL", "GOOGL", "MSFT", "NVDA", "META"],
                "category": "Technology",
            },
            {
                "name": "Blue Chips",
                "description": "Stable, well-established companies",
                "symbols": ["JNJ", "PG", "KO", "WMT", "DIS"],
                "category": "Consumer",
            },
            {
                "name": "Growth Stocks",
                "description": "High growth potential companies",
                "symbols": ["TSLA", "AMD", "COIN", "SNAP", "ROKU"],
                "category": "Growth",
            },
            {
                "name": "Dividend Stocks",
                "description": "Companies with consistent dividends",
                "symbols": ["AAPL", "MSFT", "JNJ", "PG", "KO"],
                "category": "Income",
            },
        ]

    def get_encouraging_message(self, user_id: str) -> str:
        """
        Get an encouraging message based on progress.

        Args:
            user_id: User identifier

        Returns:
            Encouraging message string
        """
        progress = self.get_progress(user_id)

        if progress.percentage == 0:
            return "🌟 Welcome! Let's get started on your investment journey."
        elif progress.percentage < 50:
            return f"🚀 Great start! You're {progress.percentage}% done with setup."
        elif progress.percentage < 100:
            return "💪 Almost there! Just a few more steps to complete your setup."
        else:
            return "🎉 Congratulations! You're all set. Happy investing!"


# Global service instance
_user_onboarding_service: Optional[UserOnboardingService] = None


def get_user_onboarding_service() -> UserOnboardingService:
    """Get or create the global user onboarding service instance."""
    global _user_onboarding_service
    if _user_onboarding_service is None:
        _user_onboarding_service = UserOnboardingService()
    return _user_onboarding_service

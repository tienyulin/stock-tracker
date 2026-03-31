"""
Alert Service - Price Alert Feature

Provides price alert management for users to monitor stock prices.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum

from app.exceptions import ValidationError


class AlertType(Enum):
    """Alert type enum."""

    PRICE_ABOVE = "PRICE_ABOVE"
    PRICE_BELOW = "PRICE_BELOW"
    PRICE_CHANGE_PERCENT = "PRICE_CHANGE_PERCENT"


@dataclass
class AlertRule:
    """Alert rule data model."""

    id: str
    user_id: str
    symbol: str
    alert_type: AlertType
    threshold: float
    enabled: bool = True
    triggered_at: int | None = None


@dataclass
class PriceAlert:
    """Price alert data model (alias for AlertRule)."""

    id: str
    user_id: str
    symbol: str
    alert_type: AlertType
    threshold: float
    enabled: bool = True
    triggered_at: int | None = None


class AlertService:
    """Service for managing price alerts."""

    MAX_ALERTS_PER_USER = 50

    def __init__(self):
        """Initialize Alert Service."""
        self._alerts: dict[str, list[AlertRule]] = {}

    async def _validate_user(self, user_id: str) -> bool:
        """Validate user exists."""
        if not user_id:
            raise ValidationError("Invalid user ID")
        return True

    def _get_user_alerts(self, user_id: str) -> list[AlertRule]:
        """Get or create user's alerts list."""
        if user_id not in self._alerts:
            self._alerts[user_id] = []
        return self._alerts[user_id]

    async def create_alert(
        self, user_id: str, symbol: str, alert_type: AlertType, threshold: float
    ) -> PriceAlert:
        """
        Create a price alert.

        Args:
            user_id: User ID.
            symbol: Stock symbol.
            alert_type: Type of alert.
            threshold: Threshold value.

        Returns:
            PriceAlert created.

        Raises:
            ValidationError: If invalid input.
            Exception: If alert limit reached.
        """
        await self._validate_user(user_id)

        if not symbol:
            raise ValidationError("Invalid symbol")

        alerts = self._get_user_alerts(user_id)

        if len(alerts) >= self.MAX_ALERTS_PER_USER:
            raise Exception(
                f"Maximum alerts per user ({self.MAX_ALERTS_PER_USER}) reached"
            )

        alert = AlertRule(
            id=str(uuid.uuid4()),
            user_id=user_id,
            symbol=symbol.upper(),
            alert_type=alert_type,
            threshold=threshold,
            enabled=True,
        )

        alerts.append(alert)
        return PriceAlert(**alert.__dict__)

    async def delete_alert(self, user_id: str, alert_id: str) -> bool:
        """
        Delete an alert.

        Args:
            user_id: User ID.
            alert_id: Alert ID.

        Returns:
            True if deleted.

        Raises:
            Exception: If alert not found.
        """
        await self._validate_user(user_id)

        alerts = self._get_user_alerts(user_id)

        for i, alert in enumerate(alerts):
            if alert.id == alert_id:
                alerts.pop(i)
                return True

        raise Exception("Alert not found")

    async def get_user_alerts(self, user_id: str) -> list[PriceAlert]:
        """
        Get all alerts for a user.

        Args:
            user_id: User ID.

        Returns:
            List of PriceAlerts.
        """
        await self._validate_user(user_id)
        alerts = self._get_user_alerts(user_id)
        return [PriceAlert(**a.__dict__) for a in alerts]

    async def toggle_alert(
        self, user_id: str, alert_id: str, enabled: bool
    ) -> PriceAlert:
        """
        Enable or disable an alert.

        Args:
            user_id: User ID.
            alert_id: Alert ID.
            enabled: New enabled state.

        Returns:
            Updated PriceAlert.

        Raises:
            Exception: If alert not found.
        """
        await self._validate_user(user_id)

        alerts = self._get_user_alerts(user_id)

        for alert in alerts:
            if alert.id == alert_id:
                alert.enabled = enabled
                return PriceAlert(**alert.__dict__)

        raise Exception("Alert not found")

    async def get_enabled_alerts(self, user_id: str) -> list[PriceAlert]:
        """
        Get only enabled alerts for a user.

        Args:
            user_id: User ID.

        Returns:
            List of enabled PriceAlerts.
        """
        await self._validate_user(user_id)
        alerts = self._get_user_alerts(user_id)
        return [PriceAlert(**a.__dict__) for a in alerts if a.enabled]

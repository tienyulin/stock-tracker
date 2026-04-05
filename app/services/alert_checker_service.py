"""
Alert Checker Service

Background service that periodically checks price conditions
and triggers notifications for active alerts.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, AlertNotification, User
from app.services.yfinance_service import YFinanceService
from app.services.line_notify_service import notify_alert_triggered
from app.services.discord_notify_service import notify_discord_alert_triggered
from app.services.email_notification_service import send_email_alert

logger = logging.getLogger(__name__)


class AlertCheckerService:
    """Service for checking and triggering price alerts."""

    def __init__(self):
        """Initialize Alert Checker Service."""
        self._running = False

    async def check_all_alerts(self, db: AsyncSession) -> dict:
        """
        Check all active alerts against current prices.

        Args:
            db: Database session

        Returns:
            Summary of alerts checked and triggered
        """
        self._running = True
        checked = 0
        triggered = 0
        errors = 0

        try:
            # Get all active alerts
            result = await db.execute(
                select(Alert, User).join(User, Alert.user_id == User.id).where(
                    and_(Alert.is_active)
                )
            )

            rows = result.fetchall()
            checked = len(rows)

            yfinance = YFinanceService()

            for alert, user in rows:
                try:
                    triggered_now = await self._check_single_alert(
                        db, alert, user, yfinance
                    )
                    if triggered_now:
                        triggered += 1
                except Exception as e:
                    logger.error(f"Error checking alert {alert.id}: {e}")
                    errors += 1

            await yfinance.close()

        finally:
            self._running = False

        return {
            "checked": checked,
            "triggered": triggered,
            "errors": errors,
            "checked_at": datetime.utcnow().isoformat(),
        }

    async def _check_single_alert(
        self,
        db: AsyncSession,
        alert: Alert,
        user: User,
        yfinance: YFinanceService,
    ) -> bool:
        """
        Check a single alert against current price.

        Returns:
            True if alert was triggered, False otherwise
        """
        try:
            quote = await yfinance.get_quote(alert.symbol)
            current_price = float(
                quote.price or quote.get("regularMarketPrice", alert.threshold)
            )
        except Exception as e:
            logger.warning(f"Failed to get quote for {alert.symbol}: {e}")
            current_price = alert.threshold  # Fallback

        # Evaluate condition
        triggered = self._evaluate_condition(
            alert.condition_type, current_price, alert.threshold
        )

        if not triggered:
            return False

        # Alert triggered! Update alert and send notifications
        alert.triggered_at = datetime.utcnow()
        alert.is_active = False

        # Create notification records
        notification_channels = self._get_enabled_channels(user)

        for channel in notification_channels:
            notification = AlertNotification(
                alert_id=alert.id,
                channel=channel,
                status="pending",
            )
            db.add(notification)

        await db.commit()

        # Send notifications (fire and forget)
        await self._send_notifications(
            db, alert, user, current_price, notification_channels
        )

        return True

    def _evaluate_condition(
        self, condition_type: str, current_price: float, threshold: float
    ) -> bool:
        """
        Evaluate if an alert condition is met.

        Args:
            condition_type: Type of condition ('above', 'below', 'change_pct')
            current_price: Current stock price
            threshold: Alert threshold

        Returns:
            True if condition is met (alert should trigger)
        """
        if condition_type == "above":
            return current_price >= threshold
        elif condition_type == "below":
            return current_price <= threshold
        elif condition_type == "change_pct":
            # For change_pct, threshold is the percentage change
            # We would need previous close to calculate actual change
            # For now, simplified check
            return abs(current_price - threshold) / threshold < 0.01
        return False

    def _get_enabled_channels(self, user: User) -> list:
        """
        Get list of enabled notification channels for a user.

        Args:
            user: User model

        Returns:
            List of enabled channel names
        """
        channels = []

        if user.line_notify_token:
            channels.append("line")

        if user.discord_webhook_url:
            channels.append("discord")

        # Email notification would require email field on user
        if hasattr(user, "email") and user.email:
            channels.append("email")

        return channels

    async def _send_notifications(
        self,
        db: AsyncSession,
        alert: Alert,
        user: User,
        current_price: float,
        channels: list,
    ):
        """
        Send notifications via all enabled channels.
        """
        for channel in channels:
            try:
                if channel == "line" and user.line_notify_token:
                    await notify_alert_triggered(
                        db=db,
                        user_id=str(user.id),
                        symbol=alert.symbol,
                        condition_type=alert.condition_type,
                        threshold=alert.threshold,
                        current_price=current_price,
                    )
                    # Update notification status
                    await self._update_notification_status(
                        db, alert.id, channel, "sent"
                    )

                elif channel == "discord" and user.discord_webhook_url:
                    await notify_discord_alert_triggered(
                        webhook_url=user.discord_webhook_url,
                        symbol=alert.symbol,
                        condition_type=alert.condition_type,
                        threshold=alert.threshold,
                        current_price=current_price,
                    )
                    await self._update_notification_status(
                        db, alert.id, channel, "sent"
                    )

                elif channel == "email":
                    await send_email_alert(
                        to_email=user.email,
                        symbol=alert.symbol,
                        condition_type=alert.condition_type,
                        threshold=alert.threshold,
                        current_price=current_price,
                    )
                    await self._update_notification_status(
                        db, alert.id, channel, "sent"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to send {channel} notification for alert {alert.id}: {e}"
                )
                await self._update_notification_status(
                    db, alert.id, channel, "failed", str(e)
                )

    async def _update_notification_status(
        self,
        db: AsyncSession,
        alert_id: str,
        channel: str,
        status: str,
        error_message: Optional[str] = None,
    ):
        """Update notification status after sending."""
        result = await db.execute(
            select(AlertNotification).where(
                and_(
                    AlertNotification.alert_id == alert_id,
                    AlertNotification.channel == channel,
                )
            )
        )
        notification = result.scalar_one_or_none()
        if notification:
            notification.status = status
            notification.sent_at = datetime.utcnow()
            notification.error_message = error_message
            await db.commit()

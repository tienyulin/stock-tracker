"""
Push Notification Service - Phase 14

Provides mobile push notification capabilities for:
- Price alert notifications
- Portfolio significant change alerts
- In-app notification history
- Notification preferences
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class NotificationType(Enum):
    """Notification type enum."""

    PRICE_ALERT = "PRICE_ALERT"
    PORTFOLIO_ALERT = "PORTFOLIO_ALERT"
    SYSTEM = "SYSTEM"


class NotificationStatus(Enum):
    """Notification delivery status."""

    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


@dataclass
class DeviceToken:
    """Device token for push notifications."""

    token: str
    platform: str  # 'fcm' (Android/FCM) or 'apns' (iOS/APNs)
    user_id: str
    device_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PushNotificationPayload:
    """Push notification payload."""

    title: str
    body: str
    data: dict = field(default_factory=dict)
    notification_type: NotificationType = NotificationType.PRICE_ALERT


@dataclass
class NotificationPreferences:
    """User notification preferences."""

    price_alerts: bool = True
    portfolio_alerts: bool = True
    push_enabled: bool = True
    quiet_hours_start: Optional[str] = None  # e.g., "22:00"
    quiet_hours_end: Optional[str] = None  # e.g., "08:00"


@dataclass
class NotificationRecord:
    """Record of a sent notification."""

    id: str
    user_id: str
    title: str
    body: str
    notification_type: NotificationType
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    delivered_to: list[str] = field(default_factory=list)  # device tokens
    error_message: Optional[str] = None


class PushNotificationService:
    """Service for sending mobile push notifications."""

    MAX_TOKENS_PER_USER = 10

    def __init__(self):
        """Initialize Push Notification Service."""
        self._tokens: dict[str, list[DeviceToken]] = {}
        self._notification_history: dict[str, list[NotificationRecord]] = {}
        self._preferences: dict[str, NotificationPreferences] = {}

    def register_device(
        self,
        user_id: str,
        token: str,
        platform: str = "fcm",
        device_name: Optional[str] = None,
    ) -> bool:
        """
        Register a device token for push notifications.

        Args:
            user_id: User identifier
            token: FCM or APNs device token
            platform: 'fcm' or 'apns'
            device_name: Human-readable device name

        Returns:
            True if registered successfully
        """
        if user_id not in self._tokens:
            self._tokens[user_id] = []

        # Check token limit
        if len(self._tokens[user_id]) >= self.MAX_TOKENS_PER_USER:
            return False

        # Check if token already registered
        for existing in self._tokens[user_id]:
            if existing.token == token:
                existing.is_active = True
                return True

        # Add new token
        device_token = DeviceToken(
            token=token,
            platform=platform,
            user_id=user_id,
            device_name=device_name,
        )
        self._tokens[user_id].append(device_token)
        return True

    def remove_device(self, user_id: str, token: str) -> bool:
        """
        Remove a device token.

        Args:
            user_id: User identifier
            token: Device token to remove

        Returns:
            True if removed successfully
        """
        if user_id not in self._tokens:
            return False

        for device in self._tokens[user_id]:
            if device.token == token:
                device.is_active = False
                return True
        return False

    def get_user_tokens(self, user_id: str, active_only: bool = True) -> list[DeviceToken]:
        """
        Get all device tokens for a user.

        Args:
            user_id: User identifier
            active_only: Only return active tokens

        Returns:
            List of device tokens
        """
        if user_id not in self._tokens:
            return []

        if active_only:
            return [t for t in self._tokens[user_id] if t.is_active]
        return self._tokens[user_id]

    def set_preferences(self, user_id: str, preferences: NotificationPreferences) -> None:
        """Set notification preferences for a user."""
        self._preferences[user_id] = preferences

    def get_preferences(self, user_id: str) -> NotificationPreferences:
        """Get notification preferences for a user."""
        if user_id not in self._preferences:
            self._preferences[user_id] = NotificationPreferences()
        return self._preferences[user_id]

    async def send_push_notification(
        self,
        user_id: str,
        payload: PushNotificationPayload,
    ) -> bool:
        """
        Send push notification to all user devices.

        Args:
            user_id: Target user
            payload: Notification payload

        Returns:
            True if sent to at least one device
        """
        tokens = self.get_user_tokens(user_id)
        if not tokens:
            return False

        # Check user preferences
        prefs = self.get_preferences(user_id)
        if not prefs.push_enabled:
            return False

        if payload.notification_type == NotificationType.PRICE_ALERT and not prefs.price_alerts:
            return False
        if payload.notification_type == NotificationType.PORTFOLIO_ALERT and not prefs.portfolio_alerts:
            return False

        # Send to all devices
        results = await asyncio.gather(
            *[self._send_to_device(user_id, token, payload) for token in tokens],
            return_exceptions=True,
        )

        # Record the notification
        record = NotificationRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=payload.title,
            body=payload.body,
            notification_type=payload.notification_type,
            status=NotificationStatus.SENT if any(results) else NotificationStatus.FAILED,
            sent_at=datetime.utcnow(),
            delivered_to=[t.token for t in tokens if results[tokens.index(t)]],
        )
        self._add_to_history(user_id, record)

        return any(r is True for r in results)

    async def _send_to_device(
        self,
        user_id: str,
        token: DeviceToken,
        payload: PushNotificationPayload,
    ) -> bool:
        """Send notification to a single device."""
        try:
            if token.platform == "fcm":
                return await send_fcm_notification(token.token, payload)
            elif token.platform == "apns":
                return await send_apns_notification(token.token, payload)
            return False
        except Exception:
            return False

    def _add_to_history(self, user_id: str, record: NotificationRecord) -> None:
        """Add notification to history."""
        if user_id not in self._notification_history:
            self._notification_history[user_id] = []
        self._notification_history[user_id].append(record)
        # Keep last 100 notifications
        if len(self._notification_history[user_id]) > 100:
            self._notification_history[user_id] = self._notification_history[user_id][-100:]

    def get_notification_history(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[NotificationRecord]:
        """Get notification history for a user."""
        if user_id not in self._notification_history:
            return []
        return self._notification_history[user_id][-limit:]


async def send_fcm_notification(token: str, payload: PushNotificationPayload) -> bool:
    """
    Send push notification via Firebase Cloud Messaging (FCM).

    Args:
        token: FCM device token
        payload: Notification payload

    Returns:
        True if sent successfully
    """
    # In production, this would use Firebase Admin SDK or HTTP API with OAuth2
    # Actual FCM integration requires:
    # 1. Firebase project ID
    # 2. Service account credentials  
    # 3. OAuth2 access token
    #
    # FCM HTTP v1 API endpoint:
    # POST https://fcm.googleapis.com/v1/projects/{project_id}/messages:send
    #
    # fcm_payload = {
    #     "message": {
    #         "token": token,
    #         "notification": {"title": payload.title, "body": payload.body},
    #         "data": payload.data,
    #     }
    # }

    # Simulate async network call
    await asyncio.sleep(0.01)
    return True


async def send_apns_notification(token: str, payload: PushNotificationPayload) -> bool:
    """
    Send push notification via Apple Push Notification Service (APNs).

    Args:
        token: APNs device token
        payload: Notification payload

    Returns:
        True if sent successfully
    """
    # APNs endpoint (use sandbox for development)
    # In production, this would use an HTTP/2 client with APNs certificate/key
    # For now, return True to indicate the notification would be sent
    # Actual APNs integration requires:
    # 1. APNs certificate or auth key
    # 2. Team ID and bundle ID
    # 3. HTTP/2 client

    # Simulate async network call
    await asyncio.sleep(0.01)
    return True


# Global service instance (for in-memory operation)
_push_notification_service: Optional[PushNotificationService] = None


def get_push_notification_service() -> PushNotificationService:
    """Get or create the global push notification service instance."""
    global _push_notification_service
    if _push_notification_service is None:
        _push_notification_service = PushNotificationService()
    return _push_notification_service

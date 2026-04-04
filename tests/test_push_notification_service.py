"""
Tests for Push Notification Service - Phase 14
"""

import pytest
from unittest.mock import patch


class TestDeviceToken:
    """Test device token model."""

    def test_device_token_creation(self):
        from app.services.push_notification_service import DeviceToken
        
        token = DeviceToken(
            token="fcm_token_123",
            platform="fcm",  # fcm, apns
            user_id="user-123",
            device_name="iPhone 15",
        )
        assert token.token == "fcm_token_123"
        assert token.platform == "fcm"
        assert token.user_id == "user-123"
        assert token.device_name == "iPhone 15"
        assert token.is_active is True


class TestPushNotificationPayload:
    """Test push notification payload."""

    def test_payload_creation(self):
        from app.services.push_notification_service import PushNotificationPayload
        
        payload = PushNotificationPayload(
            title="Price Alert",
            body="AAPL has reached $150.00",
            data={"symbol": "AAPL", "price": 150.00},
        )
        assert payload.title == "Price Alert"
        assert payload.body == "AAPL has reached $150.00"
        assert payload.data["symbol"] == "AAPL"


class TestPushNotificationService:
    """Test Push Notification Service."""

    def test_service_initialization(self):
        from app.services.push_notification_service import PushNotificationService
        
        service = PushNotificationService()
        assert service._tokens == {}

    def test_register_device(self):
        from app.services.push_notification_service import PushNotificationService
        
        service = PushNotificationService()
        service.register_device(
            user_id="user-123",
            token="fcm_token_abc",
            platform="fcm",
            device_name="Pixel 8",
        )
        assert "user-123" in service._tokens
        assert len(service._tokens["user-123"]) == 1
        assert service._tokens["user-123"][0].token == "fcm_token_abc"

    def test_register_multiple_devices(self):
        from app.services.push_notification_service import PushNotificationService
        
        service = PushNotificationService()
        service.register_device("user-123", "token1", "fcm", "iPhone")
        service.register_device("user-123", "token2", "apns", "iPad")
        
        assert len(service._tokens["user-123"]) == 2

    def test_remove_device(self):
        from app.services.push_notification_service import PushNotificationService
        
        service = PushNotificationService()
        service.register_device("user-123", "token1", "fcm", "Phone")
        service.remove_device("user-123", "token1")
        
        # Token is soft-deleted (is_active=False), not removed
        assert len(service.get_user_tokens("user-123", active_only=True)) == 0
        assert len(service.get_user_tokens("user-123", active_only=False)) == 1
        assert service.get_user_tokens("user-123", active_only=False)[0].is_active is False

    def test_get_user_tokens(self):
        from app.services.push_notification_service import PushNotificationService
        
        service = PushNotificationService()
        service.register_device("user-123", "token1", "fcm", "Phone1")
        service.register_device("user-456", "token2", "fcm", "Phone2")
        
        user_tokens = service.get_user_tokens("user-123")
        assert len(user_tokens) == 1
        assert user_tokens[0].token == "token1"

    @pytest.mark.asyncio
    async def test_send_push_notification_fcm(self):
        from app.services.push_notification_service import (
            PushNotificationService,
            PushNotificationPayload,
        )
        
        service = PushNotificationService()
        service.register_device("user-123", "fcm_token", "fcm", "Phone")
        
        payload = PushNotificationPayload(
            title="Test Alert",
            body="Test message",
        )
        
        with patch('app.services.push_notification_service.send_fcm_notification') as mock_fcm:
            mock_fcm.return_value = True
            result = await service.send_push_notification("user-123", payload)
            
            assert result is True
            mock_fcm.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_no_tokens(self):
        from app.services.push_notification_service import (
            PushNotificationService,
            PushNotificationPayload,
        )
        
        service = PushNotificationService()
        payload = PushNotificationPayload(title="Test", body="Test")
        
        result = await service.send_push_notification("nonexistent-user", payload)
        assert result is False


class TestNotificationPreferences:
    """Test notification preferences."""

    def test_preferences_defaults(self):
        from app.services.push_notification_service import NotificationPreferences
        
        prefs = NotificationPreferences()
        assert prefs.price_alerts is True
        assert prefs.portfolio_alerts is True
        assert prefs.push_enabled is True

    def test_preferences_custom(self):
        from app.services.push_notification_service import NotificationPreferences
        
        prefs = NotificationPreferences(
            price_alerts=False,
            portfolio_alerts=True,
        )
        assert prefs.price_alerts is False
        assert prefs.portfolio_alerts is True

"""
Tests for Alert Service - Price Alert Feature
"""
import pytest

from app.services.alert_service import AlertService, AlertRule, AlertType


class TestAlertRule:
    """Test data model for alert rule."""

    def test_alert_rule_creation(self):
        rule = AlertRule(
            id="alert-1",
            user_id="user-1",
            symbol="AAPL",
            alert_type=AlertType.PRICE_ABOVE,
            threshold=150.0,
            enabled=True
        )
        assert rule.symbol == "AAPL"
        assert rule.alert_type == AlertType.PRICE_ABOVE
        assert rule.threshold == 150.0


class TestAlertType:
    """Test alert type enum."""

    def test_alert_types(self):
        assert AlertType.PRICE_ABOVE.value == "PRICE_ABOVE"
        assert AlertType.PRICE_BELOW.value == "PRICE_BELOW"
        assert AlertType.PRICE_CHANGE_PERCENT.value == "PRICE_CHANGE_PERCENT"


class TestAlertService:
    """Test Alert Service for price alerts."""

    @pytest.fixture
    def service(self):
        return AlertService()

    @pytest.fixture
    def mock_user_id(self):
        return "user-123"

    @pytest.mark.asyncio
    async def test_create_price_above_alert(self, service, mock_user_id):
        """Test creating a price above alert."""
        alert = await service.create_alert(
            user_id=mock_user_id,
            symbol="AAPL",
            alert_type=AlertType.PRICE_ABOVE,
            threshold=150.0
        )

        assert alert.symbol == "AAPL"
        assert alert.alert_type == AlertType.PRICE_ABOVE
        assert alert.threshold == 150.0
        assert alert.enabled is True

    @pytest.mark.asyncio
    async def test_create_price_below_alert(self, service, mock_user_id):
        """Test creating a price below alert."""
        alert = await service.create_alert(
            user_id=mock_user_id,
            symbol="AAPL",
            alert_type=AlertType.PRICE_BELOW,
            threshold=140.0
        )

        assert alert.alert_type == AlertType.PRICE_BELOW
        assert alert.threshold == 140.0

    @pytest.mark.asyncio
    async def test_create_change_percent_alert(self, service, mock_user_id):
        """Test creating a price change percent alert."""
        alert = await service.create_alert(
            user_id=mock_user_id,
            symbol="AAPL",
            alert_type=AlertType.PRICE_CHANGE_PERCENT,
            threshold=5.0
        )

        assert alert.alert_type == AlertType.PRICE_CHANGE_PERCENT
        assert alert.threshold == 5.0

    @pytest.mark.asyncio
    async def test_delete_alert(self, service, mock_user_id):
        """Test deleting an alert."""
        alert = await service.create_alert(
            user_id=mock_user_id,
            symbol="AAPL",
            alert_type=AlertType.PRICE_ABOVE,
            threshold=150.0
        )

        result = await service.delete_alert(mock_user_id, alert.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent_alert(self, service, mock_user_id):
        """Test deleting non-existent alert."""
        with pytest.raises(Exception, match="Alert not found"):
            await service.delete_alert(mock_user_id, "invalid-id")

    @pytest.mark.asyncio
    async def test_get_user_alerts(self, service, mock_user_id):
        """Test getting user's alerts."""
        await service.create_alert(
            user_id=mock_user_id,
            symbol="AAPL",
            alert_type=AlertType.PRICE_ABOVE,
            threshold=150.0
        )
        await service.create_alert(
            user_id=mock_user_id,
            symbol="GOOGL",
            alert_type=AlertType.PRICE_BELOW,
            threshold=140.0
        )

        alerts = await service.get_user_alerts(mock_user_id)
        assert len(alerts) == 2

    @pytest.mark.asyncio
    async def test_toggle_alert(self, service, mock_user_id):
        """Test enabling/disabling an alert."""
        alert = await service.create_alert(
            user_id=mock_user_id,
            symbol="AAPL",
            alert_type=AlertType.PRICE_ABOVE,
            threshold=150.0
        )

        assert alert.enabled is True

        updated = await service.toggle_alert(mock_user_id, alert.id, False)
        assert updated.enabled is False

    @pytest.mark.asyncio
    async def test_max_alerts_limit(self, service, mock_user_id):
        """Test maximum alerts per user limit."""
        for i in range(50):
            await service.create_alert(
                user_id=mock_user_id,
                symbol=f"STOCK{i}",
                alert_type=AlertType.PRICE_ABOVE,
                threshold=100.0 + i
            )

        with pytest.raises(Exception, match="[Mm]aximum.*alerts"):
            await service.create_alert(
                user_id=mock_user_id,
                symbol="STOCK999",
                alert_type=AlertType.PRICE_ABOVE,
                threshold=200.0
            )

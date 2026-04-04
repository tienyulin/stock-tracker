"""
Tests for Broker Sync Service.
"""

import asyncio

from app.services.broker_sync_service import (
    BrokerSyncService,
    Brokerage,
    ConnectionStatus,
)


class TestBrokerageEnum:
    """Test Brokerage enum."""

    def test_brokerage_values(self):
        """Test all brokerages are defined."""
        assert Brokerage.ROBINHOOD.value == "robinhood"
        assert Brokerage.FIDELITY.value == "fidelity"
        assert Brokerage.SCHWAB.value == "schwab"
        assert Brokerage.TD_AMERITRADE.value == "td_ameritrade"
        assert Brokerage.ETRADE.value == "etrade"
        assert Brokerage.WEBULL.value == "webull"


class TestConnectionStatus:
    """Test ConnectionStatus enum."""

    def test_status_values(self):
        """Test all statuses are defined."""
        assert ConnectionStatus.PENDING.value == "pending"
        assert ConnectionStatus.CONNECTED.value == "connected"
        assert ConnectionStatus.SYNCING.value == "syncing"
        assert ConnectionStatus.ERROR.value == "error"
        assert ConnectionStatus.DISCONNECTED.value == "disconnected"


class TestBrokerSyncService:
    """Test Broker Sync Service."""

    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = BrokerSyncService(client_id="test", client_secret="secret")
        assert service.client_id == "test"
        assert service.client_secret == "secret"

    def test_create_connection(self):
        """Test creating a broker connection."""
        service = BrokerSyncService()
        
        connection = asyncio.run(
            service.create_connection(
                user_id="user123",
                brokerage=Brokerage.ROBINHOOD,
                access_token="encrypted_access",
                refresh_token="encrypted_refresh",
                broker_account_id="RH12345",
            )
        )
        
        assert connection.user_id == "user123"
        assert connection.brokerage == Brokerage.ROBINHOOD
        assert connection.status == ConnectionStatus.CONNECTED
        assert connection.broker_account_id == "RH12345"

    def test_get_user_connections(self):
        """Test retrieving user connections."""
        service = BrokerSyncService()
        
        # Create a connection
        asyncio.run(
            service.create_connection(
                user_id="user123",
                brokerage=Brokerage.FIDELITY,
                access_token="token",
                refresh_token="refresh",
                broker_account_id="FID123",
            )
        )
        
        connections = asyncio.run(
            service.get_user_connections("user123")
        )
        
        assert len(connections) == 1
        assert connections[0].brokerage == Brokerage.FIDELITY

    def test_delete_connection(self):
        """Test deleting a connection."""
        service = BrokerSyncService()
        
        # Create connection
        conn = asyncio.run(
            service.create_connection(
                user_id="user123",
                brokerage=Brokerage.SCHWAB,
                access_token="token",
                refresh_token="refresh",
                broker_account_id="SCHWAB123",
            )
        )
        
        # Delete it
        deleted = asyncio.run(
            service.delete_connection(conn.connection_id, "user123")
        )
        
        assert deleted is True
        assert conn.status == ConnectionStatus.DISCONNECTED

    def test_map_brokerage_holdings(self):
        """Test mapping brokerage holdings to our format."""
        service = BrokerSyncService()
        
        result = service.map_brokerage_holdings(
            brokerage_symbol="AAPL",
            quantity=100.0,
            security_type="STOCK",
            cost_basis=15000.0,
        )
        
        assert result["symbol"] == "AAPL"
        assert result["quantity"] == 100.0
        assert result["asset_type"] == "STOCK"
        assert result["cost_basis"] == 15000.0

    def test_map_brokerage_holdings_symbol_normalization(self):
        """Test symbol normalization (BRK.B -> BRK-B)."""
        service = BrokerSyncService()
        
        result = service.map_brokerage_holdings(
            brokerage_symbol="BRK.B",
            quantity=50.0,
            security_type="STOCK",
        )
        
        assert result["symbol"] == "BRK-B"


class TestBrokerSyncEndpoints:
    """Test broker sync API endpoints."""

    def test_endpoint_structure(self):
        """Verify endpoints are defined."""
        from app.api.v1.broker_sync import router
        
        routes = [r.path for r in router.routes]
        assert any("/connections" in str(r) for r in routes)
        assert any("/oauth-url" in str(r) for r in routes)
        assert any("/sync" in str(r) for r in routes)
        assert any("/supported-brokers" in str(r) for r in routes)

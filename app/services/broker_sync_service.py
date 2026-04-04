"""
Broker Sync Service

Provides automated portfolio import from brokerage accounts using OAuth.
Supports SnapTrade API for unified brokerage connections.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class Brokerage(Enum):
    """Supported brokerage firms."""
    ROBINHOOD = "robinhood"
    FIDELITY = "fidelity"
    SCHWAB = "schwab"
    TD_AMERITRADE = "td_ameritrade"
    ETRADE = "etrade"
    WEBULL = "webull"


class ConnectionStatus(Enum):
    """Broker connection status."""
    PENDING = "pending"
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"
    DISCONNECTED = "disconnected"


@dataclass
class BrokerConnection:
    """A brokerage account connection."""
    connection_id: str
    user_id: str
    brokerage: Brokerage
    status: ConnectionStatus
    broker_account_id: Optional[str] = None  # Account ID at brokerage
    encrypted_access_token: Optional[str] = None
    encrypted_refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class BrokerHolding:
    """A holding imported from a brokerage."""
    symbol: str
    quantity: float
    account_id: str
    security_type: str = "STOCK"  # STOCK, ETF, MUTUAL_FUND, OPTION, CRYPTO
    cost_basis: Optional[float] = None
    current_value: Optional[float] = None


@dataclass
class SyncResult:
    """Result of a broker sync operation."""
    connection_id: str
    success: bool
    holdings_imported: int
    holdings_updated: int
    holdings_failed: int
    last_sync: datetime
    error_message: Optional[str] = None


class BrokerSyncService:
    """
    Service for connecting to brokerages and syncing holdings.
    
    Uses SnapTrade API for unified brokerage connections.
    """

    # SnapTrade API configuration (would use environment variables in production)
    SNAPTRADE_API_URL = "https://api.snaptrade.com/v1"
    
    # OAuth callback URL
    OAUTH_CALLBACK_URL = "/api/v1/broker-sync/callback"

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialize Broker Sync Service.
        
        Args:
            client_id: SnapTrade client ID
            client_secret: SnapTrade client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self._connections: dict[str, BrokerConnection] = {}  # In-memory for demo

    def get_oauth_url(self, brokerage: Brokerage, user_id: str, redirect_uri: str) -> str:
        """
        Generate OAuth URL for brokerage connection.
        
        Args:
            brokerage: The brokerage to connect to
            user_id: The user connecting
            redirect_uri: OAuth callback URL
            
        Returns:
            OAuth authorization URL
        """
        # Generate state token for CSRF protection
        state = str(uuid.uuid4())
        
        # In production, this would call SnapTrade OAuth
        # For now, return a placeholder URL structure
        base_urls = {
            Brokerage.ROBINHOOD: "https://robinhood.com/oauth2/authorize",
            Brokerage.FIDELITY: "https://www.fidelity.com/oauth2/authorize",
            Brokerage.SCHWAB: "https://www.schwab.com/oauth2/authorize",
            Brokerage.TD_AMERITRADE: "https://auth.tdameritrade.com/oauth2/authorize",
            Brokerage.ETRADE: "https://us.etrade.com/oauth2/authorize",
            Brokerage.WEBULL: "https://www.webull.com/oauth2/authorize",
        }
        
        # In production, construct proper OAuth URL with client_id, redirect_uri, state, etc.
        return f"{base_urls.get(brokerage, 'https://example.com/oauth')}?client_id={self.client_id}&redirect_uri={redirect_uri}&state={state}"

    async def create_connection(
        self,
        user_id: str,
        brokerage: Brokerage,
        access_token: str,
        refresh_token: str,
        broker_account_id: str,
        expires_at: Optional[datetime] = None,
    ) -> BrokerConnection:
        """
        Create a new brokerage connection.
        
        Args:
            user_id: User ID
            brokerage: Brokerage being connected
            access_token: Encrypted OAuth access token
            refresh_token: Encrypted OAuth refresh token
            broker_account_id: Account ID at the brokerage
            expires_at: Token expiration time
            
        Returns:
            Created BrokerConnection
        """
        connection_id = str(uuid.uuid4())
        
        connection = BrokerConnection(
            connection_id=connection_id,
            user_id=user_id,
            brokerage=brokerage,
            status=ConnectionStatus.CONNECTED,
            broker_account_id=broker_account_id,
            encrypted_access_token=access_token,
            encrypted_refresh_token=refresh_token,
            token_expires_at=expires_at,
            last_sync_at=datetime.utcnow(),
        )
        
        self._connections[connection_id] = connection
        return connection

    async def get_user_connections(self, user_id: str) -> list[BrokerConnection]:
        """Get all broker connections for a user."""
        return [
            c for c in self._connections.values()
            if c.user_id == user_id
        ]

    async def get_connection(self, connection_id: str, user_id: str) -> Optional[BrokerConnection]:
        """Get a specific connection."""
        conn = self._connections.get(connection_id)
        if conn and conn.user_id == user_id:
            return conn
        return None

    async def delete_connection(self, connection_id: str, user_id: str) -> bool:
        """
        Delete/disconnect a brokerage connection.
        
        Args:
            connection_id: Connection to delete
            user_id: User requesting deletion
            
        Returns:
            True if deleted, False if not found
        """
        conn = self._connections.get(connection_id)
        if conn and conn.user_id == user_id:
            conn.status = ConnectionStatus.DISCONNECTED
            return True
        return False

    async def sync_holdings(self, connection_id: str) -> SyncResult:
        """
        Sync holdings from a brokerage connection.
        
        Args:
            connection_id: Connection to sync
            
        Returns:
            SyncResult with imported holdings
        """
        conn = self._connections.get(connection_id)
        if not conn:
            return SyncResult(
                connection_id=connection_id,
                success=False,
                holdings_imported=0,
                holdings_updated=0,
                holdings_failed=0,
                last_sync=datetime.utcnow(),
                error_message="Connection not found"
            )
        
        conn.status = ConnectionStatus.SYNCING
        
        try:
            # In production, this would call SnapTrade API to fetch holdings
            # For now, return placeholder holdings
            holdings = await self._fetch_brokerage_holdings(conn)
            
            # Process holdings...
            imported = len(holdings)
            
            conn.last_sync_at = datetime.utcnow()
            conn.status = ConnectionStatus.CONNECTED
            
            return SyncResult(
                connection_id=connection_id,
                success=True,
                holdings_imported=imported,
                holdings_updated=0,
                holdings_failed=0,
                last_sync=conn.last_sync_at,
            )
            
        except Exception as e:
            conn.status = ConnectionStatus.ERROR
            conn.error_message = str(e)
            return SyncResult(
                connection_id=connection_id,
                success=False,
                holdings_imported=0,
                holdings_updated=0,
                holdings_failed=0,
                last_sync=datetime.utcnow(),
                error_message=str(e)
            )

    async def _fetch_brokerage_holdings(self, connection: BrokerConnection) -> list[BrokerHolding]:
        """
        Fetch holdings from brokerage API.
        
        In production, this would call SnapTrade API.
        """
        # Placeholder - would call SnapTrade API
        # SnapTrade returns holdings in format:
        # {
        #   "holdings": [
        #     {"symbol": "AAPL", "quantity": 100, "accountId": "..."},
        #     {"symbol": "GOOGL", "quantity": 50, "accountId": "..."},
        #   ]
        # }
        
        return [
            BrokerHolding(
                symbol="AAPL",
                quantity=100.0,
                account_id=connection.broker_account_id or "demo",
                security_type="STOCK",
            )
        ]

    def map_brokerage_holdings(
        self,
        brokerage_symbol: str,
        quantity: float,
        security_type: str,
        cost_basis: Optional[float] = None,
    ) -> dict:
        """
        Map brokerage holding to our portfolio model.
        
        Args:
            brokerage_symbol: Symbol as reported by brokerage
            quantity: Number of shares
            security_type: Type from brokerage
            cost_basis: Cost basis if available
            
        Returns:
            Dict suitable for portfolio service
        """
        # Map to our symbol if different
        # Some brokerages use different symbols (e.g., "BRK.B" vs "BRK-B")
        symbol_map = {
            "BRK.B": "BRK-B",
            "BRK.A": "BRK-A",
        }
        
        symbol = symbol_map.get(brokerage_symbol, brokerage_symbol)
        
        # Map security types
        asset_type_map = {
            "STOCK": "STOCK",
            "ETF": "ETF",
            "MUTUAL_FUND": "MUTUAL_FUND",
            "OPTION": "OPTION",
            "CRYPTO": "CRYPTO",
        }
        
        return {
            "symbol": symbol,
            "quantity": quantity,
            "asset_type": asset_type_map.get(security_type, "STOCK"),
            "cost_basis": cost_basis,
        }


# Global instance
broker_sync_service = BrokerSyncService()

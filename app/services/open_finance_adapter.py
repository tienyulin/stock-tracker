"""
Open Finance Unified Adapter

Provides a unified interface for aggregating financial data from multiple
Open Finance providers (E.Sun Bank, Yodlee, Plaid) and normalizing it
into a PersonalFinancialProfile.
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

import httpx
from pydantic import Field

from app.schemas.agent_schemas import (
    AccountBalance,
    HoldingAsset,
    OpenFinanceConnection,
    OpenFinanceProvider,
    PersonalFinancialProfile,
    ConnectionStatus,
)


class OpenFinanceAdapterError(Exception):
    """Base exception for Open Finance adapter errors."""

    pass


class ProviderConnectionError(OpenFinanceAdapterError):
    """Error connecting to a provider."""

    pass


class ProviderAuthenticationError(OpenFinanceAdapterError):
    """Error authenticating with a provider."""

    pass


class BaseOpenFinanceAdapter(ABC):
    """Abstract base class for Open Finance providers."""

    provider: OpenFinanceProvider

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize the adapter with credentials."""
        self.api_key = api_key or os.environ.get(f"{self.provider.name}_API_KEY")
        self.api_secret = api_secret or os.environ.get(f"{self.provider.name}_API_SECRET")

    @abstractmethod
    async def connect(self, user_id: UUID, auth_code: str) -> OpenFinanceConnection:
        """Connect a user's account to the provider.

        Args:
            user_id: The user's ID.
            auth_code: Authorization code from OAuth flow.

        Returns:
            OpenFinanceConnection object with connection details.
        """
        pass

    @abstractmethod
    async def disconnect(self, connection: OpenFinanceConnection) -> bool:
        """Disconnect a user's account from the provider.

        Args:
            connection: The connection to disconnect.

        Returns:
            True if successful.
        """
        pass

    @abstractmethod
    async def sync_accounts(self, connection: OpenFinanceConnection) -> list[AccountBalance]:
        """Sync and retrieve account balances.

        Args:
            connection: The active connection.

        Returns:
            List of AccountBalance objects.
        """
        pass

    @abstractmethod
    async def sync_holdings(self, connection: OpenFinanceConnection) -> list[HoldingAsset]:
        """Sync and retrieve holdings.

        Args:
            connection: The active connection.

        Returns:
            List of HoldingAsset objects.
        """
        pass

    async def build_profile(
        self,
        user_id: UUID,
        connections: list[OpenFinanceConnection],
    ) -> PersonalFinancialProfile:
        """Build a comprehensive financial profile from all connections.

        Args:
            user_id: The user's ID.
            connections: List of active Open Finance connections.

        Returns:
            PersonalFinancialProfile with aggregated data.
        """
        all_holdings: list[HoldingAsset] = []
        all_accounts: list[AccountBalance] = []

        for conn in connections:
            if conn.status != ConnectionStatus.ACTIVE:
                continue

            try:
                accounts = await self.sync_accounts(conn)
                all_accounts.extend(accounts)

                holdings = await self.sync_holdings(conn)
                all_holdings.extend(holdings)
            except OpenFinanceAdapterError:
                # Log but continue with other connections
                pass

        # Calculate totals
        total_assets = sum(a.balance for a in all_accounts if a.balance > 0)
        total_liabilities = sum(abs(a.balance) for a in all_accounts if a.balance < 0)
        total_cash = sum(
            a.balance for a in all_accounts if a.account_type in ("checking", "savings")
        )
        total_investments = sum(
            a.balance for a in all_accounts if a.account_type == "investment"
        )
        total_debt = sum(
            abs(a.balance) for a in all_accounts if a.account_type in ("credit", "loan")
        )

        return PersonalFinancialProfile(
            user_id=user_id,
            total_net_worth=total_assets - total_liabilities,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_cash=total_cash,
            total_investments=total_investments,
            total_debt=total_debt,
            holdings=all_holdings,
            accounts=all_accounts,
            last_updated=datetime.now(),
            connections=connections,
        )


class ESunBankAdapter(BaseOpenFinanceAdapter):
    """Adapter for E.Sun Bank Open Finance API (Taiwan).

    E.Sun Bank provides Open Banking APIs for account aggregation
    in the Taiwan market.
    """

    provider = OpenFinanceProvider.ESUN_BANK
    BASE_URL = "https://openbank.esunbank.com.tw/api/v1"

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        super().__init__(api_key, api_secret)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def connect(self, user_id: UUID, auth_code: str) -> OpenFinanceConnection:
        """Connect to E.Sun Bank using OAuth authorization code.

        Args:
            user_id: User's ID.
            auth_code: OAuth authorization code from E.Sun Bank.

        Returns:
            OpenFinanceConnection with active status.
        """
        if not self.api_key:
            raise ProviderAuthenticationError("E.Sun Bank API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "auth_code": auth_code,
            "user_id": str(user_id),
        }

        try:
            response = await self.client.post(
                f"{self.BASE_URL}/connect",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ProviderAuthenticationError("Invalid E.Sun Bank credentials")
            raise ProviderConnectionError(f"E.Sun Bank connection failed: {e}")
        except httpx.RequestError as e:
            raise ProviderConnectionError(f"E.Sun Bank request failed: {e}")

        return OpenFinanceConnection(
            id=uuid4(),
            user_id=user_id,
            provider=self.provider,
            status=ConnectionStatus.ACTIVE,
            institution_name="E.Sun Bank",
            institution_id=data.get("institution_id", "ESUN"),
            account_ids=data.get("account_ids", []),
            permissions=["READ_BALANCES", "READ_HOLDINGS", "READ_TRANSACTIONS"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    async def disconnect(self, connection: OpenFinanceConnection) -> bool:
        """Disconnect from E.Sun Bank.

        Args:
            connection: The connection to disconnect.

        Returns:
            True if successful.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            response = await self.client.delete(
                f"{self.BASE_URL}/connect/{connection.id}",
                headers=headers,
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    async def sync_accounts(self, connection: OpenFinanceConnection) -> list[AccountBalance]:
        """Fetch account balances from E.Sun Bank.

        Args:
            connection: Active E.Sun Bank connection.

        Returns:
            List of AccountBalance objects.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        accounts: list[AccountBalance] = []

        for account_id in connection.account_ids:
            try:
                response = await self.client.get(
                    f"{self.BASE_URL}/accounts/{account_id}/balances",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                account_type = self._normalize_account_type(data.get("account_type", ""))
                balance = float(data.get("balance", 0))

                accounts.append(
                    AccountBalance(
                        account_id=account_id,
                        account_name=data.get("account_name", f"E.Sun Account {account_id}"),
                        account_type=account_type,
                        balance=balance,
                        currency=data.get("currency", "TWD"),
                        provider=self.provider,
                        institution_name="E.Sun Bank",
                        last_updated=datetime.now(),
                    )
                )
            except httpx.HTTPError:
                pass

        return accounts

    async def sync_holdings(self, connection: OpenFinanceConnection) -> list[HoldingAsset]:
        """Fetch investment holdings from E.Sun Bank.

        Args:
            connection: Active E.Sun Bank connection.

        Returns:
            List of HoldingAsset objects.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        holdings: list[HoldingAsset] = []

        for account_id in connection.account_ids:
            try:
                response = await self.client.get(
                    f"{self.BASE_URL}/accounts/{account_id}/holdings",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                for holding in data.get("holdings", []):
                    holdings.append(
                        HoldingAsset(
                            symbol=holding.get("symbol", ""),
                            name=holding.get("name"),
                            quantity=float(holding.get("quantity", 0)),
                            current_value=float(holding.get("market_value", 0)),
                            cost_basis=float(holding.get("cost_basis", 0)),
                            unrealized_gain=float(holding.get("unrealized_gain", 0)),
                            unrealized_gain_percent=float(
                                holding.get("unrealized_gain_percent", 0)
                            ),
                            asset_class=self._classify_asset(holding.get("symbol", "")),
                            account_id=account_id,
                            provider=self.provider,
                        )
                    )
            except httpx.HTTPError:
                pass

        return holdings

    def _normalize_account_type(self, esun_type: str) -> str:
        """Normalize E.Sun account type to standard types."""
        mapping = {
            "CHECKING": "checking",
            "SAVINGS": "savings",
            "INVESTMENT": "investment",
            "CREDIT": "credit",
            "LOAN": "loan",
            "MONEY_MARKET": "cash",
        }
        return mapping.get(esun_type.upper(), "other")

    def _classify_asset(self, symbol: str) -> str:
        """Classify asset based on symbol pattern."""
        if symbol.startswith(("2330", "2317", "2303", "2454")):
            return "stock"  # Taiwan stocks
        if symbol.startswith(("00", "^")):
            return "stock"  # Indices like ^TWII
        if symbol.endswith((".TW", ".TWO")):
            return "stock"
        return "other"


class YodleeAdapter(BaseOpenFinanceAdapter):
    """Adapter for Yodlee aggregation API.

    Yodlee provides account aggregation services used by many
    financial institutions and fintech apps globally.
    """

    provider = OpenFinanceProvider.YODLEE
    BASE_URL = "https://production.yodlee.com/fastlink"

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        super().__init__(api_key, api_secret)
        self.client = httpx.AsyncClient(timeout=60.0)
        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        """Obtain a new access token via client credentials flow."""
        if self._access_token:
            return self._access_token

        if not self.api_key or not self.api_secret:
            raise ProviderAuthenticationError("Yodlee API credentials not configured")

        response = await self.client.post(
            "https://api.yodlee.com/ysl/authToken",
            auth=(self.api_key, self.api_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"},
        )
        response.raise_for_status()
        self._access_token = response.json()["token"]["accessToken"]
        return self._access_token

    async def connect(self, user_id: UUID, auth_code: str) -> OpenFinanceConnection:
        """Connect to Yodlee via provider's OAuth or fastlink flow.

        Args:
            user_id: User's ID.
            auth_code: Fastlink access token or provider auth code.

        Returns:
            OpenFinanceConnection with active status.
        """
        access_token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # Register fastlink user session
        payload = {
            "userId": str(user_id),
            "accessTokens": [auth_code],
        }

        try:
            response = await self.client.post(
                "https://api.yodlee.com/ysl/v1/user/accessTokens",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ProviderAuthenticationError("Yodlee authentication failed")
            raise ProviderConnectionError(f"Yodlee connection failed: {e}")
        except httpx.RequestError as e:
            raise ProviderConnectionError(f"Yodlee request failed: {e}")

        account_ids = [a["id"] for a in data.get("account", [])]

        return OpenFinanceConnection(
            id=uuid4(),
            user_id=user_id,
            provider=self.provider,
            status=ConnectionStatus.ACTIVE,
            institution_name="Yodlee Aggregated",
            institution_id="YODLEE",
            account_ids=[str(aid) for aid in account_ids],
            permissions=["READ_BALANCES", "READ_HOLDINGS", "READ_TRANSACTIONS"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    async def disconnect(self, connection: OpenFinanceConnection) -> bool:
        """Remove Yodlee account linkage.

        Args:
            connection: The connection to remove.

        Returns:
            True if successful.
        """
        access_token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            for account_id in connection.account_ids:
                await self.client.delete(
                    f"https://api.yodlee.com/ysl/v1/accounts/{account_id}",
                    headers=headers,
                )
            return True
        except httpx.HTTPError:
            return False

    async def sync_accounts(self, connection: OpenFinanceConnection) -> list[AccountBalance]:
        """Fetch accounts and balances from Yodlee.

        Args:
            connection: Active Yodlee connection.

        Returns:
            List of AccountBalance objects.
        """
        access_token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        accounts: list[AccountBalance] = []

        try:
            response = await self.client.get(
                "https://api.yodlee.com/ysl/v1/accounts",
                headers=headers,
                params={"accountIds": ",".join(connection.account_ids)},
            )
            response.raise_for_status()
            data = response.json()

            for acct in data.get("account", []):
                accounts.append(
                    AccountBalance(
                        account_id=str(acct["id"]),
                        account_name=acct.get("accountName", "Yodlee Account"),
                        account_type=self._normalize_account_type(acct.get("accountType", "")),
                        balance=float(acct.get("balance", {}).get("amount", 0)),
                        currency=acct.get("balance", {}).get("currency", "USD"),
                        provider=self.provider,
                        institution_name=acct.get("providerName", "Yodlee"),
                        last_updated=datetime.now(),
                    )
                )
        except httpx.HTTPError:
            pass

        return accounts

    async def sync_holdings(self, connection: OpenFinanceConnection) -> list[HoldingAsset]:
        """Fetch investment holdings from Yodlee.

        Args:
            connection: Active Yodlee connection.

        Returns:
            List of HoldingAsset objects.
        """
        access_token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        holdings: list[HoldingAsset] = []

        try:
            response = await self.client.get(
                "https://api.yodlee.com/ysl/v1/holdings",
                headers=headers,
                params={"accountIds": ",".join(connection.account_ids)},
            )
            response.raise_for_status()
            data = response.json()

            for holding in data.get("holding", []):
                holdings.append(
                    HoldingAsset(
                        symbol=holding.get("symbol", ""),
                        name=holding.get("description", {}).get("value"),
                        quantity=float(holding.get("quantity", 0)),
                        current_value=float(holding.get("marketValue", 0)),
                        cost_basis=float(holding.get("costBasis", {}).get("amount", 0)),
                        unrealized_gain=float(holding.get("gainLoss", 0)),
                        unrealized_gain_percent=float(
                            holding.get("gainLossPercent", 0)
                        ),
                        asset_class=self._classify_asset(holding.get("securityType", "")),
                        account_id=str(holding.get("accountId", "")),
                        provider=self.provider,
                    )
                )
        except httpx.HTTPError:
            pass

        return holdings

    def _normalize_account_type(self, yodlee_type: str) -> str:
        """Normalize Yodlee account type to standard types."""
        mapping = {
            "CHECKING": "checking",
            "SAVINGS": "savings",
            "INVESTMENT": "investment",
            "BROKERAGE_MARGIN": "investment",
            "CREDIT_CARD": "credit",
            "LOAN": "loan",
            "MORTGAGE": "loan",
        }
        return mapping.get(yodlee_type.upper(), "other")

    def _classify_asset(self, security_type: str) -> str:
        """Classify asset based on Yodlee security type."""
        mapping = {
            "EQUITY": "stock",
            "MUTUAL_FUND": "stock",
            "ETF": "stock",
            "BOND": "bond",
            "FIXED_INCOME": "bond",
            "CASH": "cash",
            "OPTION": "stock",
        }
        return mapping.get(security_type.upper(), "other")


class PlaidAdapter(BaseOpenFinanceAdapter):
    """Adapter for Plaid API.

    Plaid is a widely-used US fintech platform for financial
    data aggregation. This adapter wraps Plaid for use in Taiwan
    markets with international banks.
    """

    provider = OpenFinanceProvider.PLAID
    BASE_URL = "https://production.plaid.com"

    def __init__(self, client_id: Optional[str] = None, secret: Optional[str] = None):
        env_client_id = client_id or os.environ.get("PLAID_CLIENT_ID")
        env_secret = secret or os.environ.get("PLAID_SECRET")
        super().__init__(env_client_id, env_secret)
        self.client = httpx.AsyncClient(timeout=60.0)

    async def connect(self, user_id: UUID, public_token: str) -> OpenFinanceConnection:
        """Exchange a Plaid public token for an access token.

        Args:
            user_id: User's ID.
            public_token: Plaid public token from Link flow.

        Returns:
            OpenFinanceConnection with active status.
        """
        if not self.api_key or not self.api_secret:
            raise ProviderAuthenticationError("Plaid credentials not configured")

        try:
            response = await self.client.post(
                f"{self.BASE_URL}/item/public_token/exchange",
                json={
                    "client_id": self.api_key,
                    "secret": self.api_secret,
                    "public_token": public_token,
                },
            )
            response.raise_for_status()
            data = response.json()
            # Token obtained successfully (for future use with Plaid API)
            # Response data contains access_token and item_id needed for subsequent calls
            item_id = data.get("item_id", str(uuid4()))
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise ProviderAuthenticationError("Invalid Plaid public token")
            raise ProviderConnectionError(f"Plaid connection failed: {e}")
        except httpx.RequestError as e:
            raise ProviderConnectionError(f"Plaid request failed: {e}")

        return OpenFinanceConnection(
            id=uuid4(),
            user_id=user_id,
            provider=self.provider,
            status=ConnectionStatus.ACTIVE,
            institution_name="Plaid Linked",
            institution_id=item_id,
            account_ids=[],
            permissions=["READ_BALANCES", "READ_HOLDINGS", "READ_TRANSACTIONS"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    async def disconnect(self, connection: OpenFinanceConnection) -> bool:
        """Remove Plaid item linkage.

        Args:
            connection: The connection to remove.

        Returns:
            True if successful.
        """
        if not self.api_key or not self.api_secret:
            return False

        try:
            # Item ID stored in institution_id for Plaid
            response = await self.client.post(
                f"{self.BASE_URL}/item/remove",
                json={
                    "client_id": self.api_key,
                    "secret": self.api_secret,
                    "item_id": connection.institution_id,
                },
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    async def sync_accounts(self, connection: OpenFinanceConnection) -> list[AccountBalance]:
        """Fetch accounts from Plaid.

        Args:
            connection: Active Plaid connection.

        Returns:
            List of AccountBalance objects.
        """
        if not self.api_key or not self.api_secret:
            return []

        headers = {"Content-Type": "application/json"}
        accounts: list[AccountBalance] = []

        # Get accounts for the item
        try:
            response = await self.client.post(
                f"{self.BASE_URL}/accounts/get",
                json={
                    "client_id": self.api_key,
                    "secret": self.api_secret,
                    "item_id": connection.institution_id,
                },
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            for acct in data.get("accounts", []):
                accounts.append(
                    AccountBalance(
                        account_id=acct["account_id"],
                        account_name=acct.get("name", "Plaid Account"),
                        account_type=self._normalize_account_type(acct.get("type", "")),
                        balance=float(acct.get("balances", {}).get("current", 0)),
                        currency=acct.get("balances", {}).get("iso_currency_code", "USD"),
                        provider=self.provider,
                        institution_name=data.get("item", {}).get("institution_name", "Plaid"),
                        last_updated=datetime.now(),
                    )
                )
        except httpx.HTTPError:
            pass

        return accounts

    async def sync_holdings(self, connection: OpenFinanceConnection) -> list[HoldingAsset]:
        """Fetch investment holdings from Plaid.

        Args:
            connection: Active Plaid connection.

        Returns:
            List of HoldingAsset objects.
        """
        if not self.api_key or not self.api_secret:
            return []

        headers = {"Content-Type": "application/json"}
        holdings: list[HoldingAsset] = []

        try:
            response = await self.client.post(
                f"{self.BASE_URL}/investments/holdings/get",
                json={
                    "client_id": self.api_key,
                    "secret": self.api_secret,
                    "item_id": connection.institution_id,
                },
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            for holding in data.get("holdings", []):
                security = next(
                    (s for s in data.get("securities", []) if s["security_id"] == holding["security_id"]),
                    {},
                )
                holdings.append(
                    HoldingAsset(
                        symbol=security.get("ticker_symbol", ""),
                        name=security.get("name"),
                        quantity=float(holding.get("quantity", 0)),
                        current_value=float(holding.get("market_value", 0)),
                        cost_basis=float(holding.get("cost_basis", 0)),
                        unrealized_gain=float(holding.get("institution_value", 0))
                        - float(holding.get("cost_basis", 0)),
                        unrealized_gain_percent=0,  # Plaid doesn't provide directly
                        asset_class=self._classify_asset(security.get("type", "")),
                        account_id=holding.get("account_id", ""),
                        provider=self.provider,
                    )
                )
        except httpx.HTTPError:
            pass

        return holdings

    def _normalize_account_type(self, plaid_type: str) -> str:
        """Normalize Plaid account type to standard types."""
        mapping = {
            "depository": "checking",
            "investment": "investment",
            "credit": "credit",
            "loan": "loan",
            "brokerage": "investment",
        }
        return mapping.get(plaid_type.lower(), "other")

    def _classify_asset(self, security_type: str) -> str:
        """Classify asset based on Plaid security type."""
        mapping = {
            "equity": "stock",
            "etf": "stock",
            "mutual fund": "stock",
            "bond": "bond",
            "cash": "cash",
            "option": "stock",
            "cryptocurrency": "crypto",
        }
        return mapping.get(security_type.lower(), "other")


class OpenFinanceAdapterFactory:
    """Factory for creating Open Finance adapters."""

    _adapters: dict[OpenFinanceProvider, type[BaseOpenFinanceAdapter]] = {
        OpenFinanceProvider.ESUN_BANK: ESunBankAdapter,
        OpenFinanceProvider.YODLEE: YodleeAdapter,
        OpenFinanceProvider.PLAID: PlaidAdapter,
    }

    @classmethod
    def create(cls, provider: OpenFinanceProvider) -> BaseOpenFinanceAdapter:
        """Create an adapter for the given provider.

        Args:
            provider: The Open Finance provider.

        Returns:
            Configured adapter instance.
        """
        adapter_class = cls._adapters.get(provider)
        if not adapter_class:
            raise ValueError(f"Unknown provider: {provider}")
        return adapter_class()

    @classmethod
    def create_all(cls) -> dict[OpenFinanceProvider, BaseOpenFinanceAdapter]:
        """Create all configured adapters.

        Returns:
            Dict of provider -> adapter instances.
        """
        return {provider: cls.create(provider) for provider in cls._adapters}

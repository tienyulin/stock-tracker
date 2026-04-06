"""
Tests for Open Finance Adapter
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.schemas.agent_schemas import (
    OpenFinanceProvider,
    OpenFinanceConnection,
    ConnectionStatus,
    AccountBalance,
    HoldingAsset,
    PersonalFinancialProfile,
)
from app.services.open_finance_adapter import (
    BaseOpenFinanceAdapter,
    OpenFinanceAdapterFactory,
    ESunBankAdapter,
    YodleeAdapter,
    PlaidAdapter,
    ProviderConnectionError,
    ProviderAuthenticationError,
)


class TestOpenFinanceAdapterFactory:
    """Tests for the adapter factory."""

    def test_create_esun_adapter(self):
        """Factory should create E.Sun Bank adapter."""
        adapter = OpenFinanceAdapterFactory.create(OpenFinanceProvider.ESUN_BANK)
        assert isinstance(adapter, ESunBankAdapter)
        assert adapter.provider == OpenFinanceProvider.ESUN_BANK

    def test_create_yodlee_adapter(self):
        """Factory should create Yodlee adapter."""
        adapter = OpenFinanceAdapterFactory.create(OpenFinanceProvider.YODLEE)
        assert isinstance(adapter, YodleeAdapter)
        assert adapter.provider == OpenFinanceProvider.YODLEE

    def test_create_plaid_adapter(self):
        """Factory should create Plaid adapter."""
        adapter = OpenFinanceAdapterFactory.create(OpenFinanceProvider.PLAID)
        assert isinstance(adapter, PlaidAdapter)
        assert adapter.provider == OpenFinanceProvider.PLAID

    def test_create_unknown_provider_raises(self):
        """Unknown provider should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            OpenFinanceAdapterFactory.create("UNKNOWN" + OpenFinanceProvider.ESUN_BANK.name)

    def test_create_all_returns_dict(self):
        """create_all should return dict of all adapters."""
        adapters = OpenFinanceAdapterFactory.create_all()
        assert isinstance(adapters, dict)
        assert OpenFinanceProvider.ESUN_BANK in adapters
        assert OpenFinanceProvider.YODLEE in adapters
        assert OpenFinanceProvider.PLAID in adapters


class TestESunBankAdapter:
    """Tests for E.Sun Bank adapter."""

    @pytest.fixture
    def adapter(self):
        """Create E.Sun Bank adapter with mock credentials."""
        return ESunBankAdapter(api_key="test_key", api_secret="test_secret")

    @pytest.mark.asyncio
    async def test_connect_success(self, adapter):
        """Should successfully connect with valid auth code."""
        user_id = uuid4()
        mock_response = {
            "institution_id": "ESUN",
            "account_ids": ["acc1", "acc2"],
        }

        with patch.object(adapter.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=mock_response),
            )

            conn = await adapter.connect(user_id, "auth_code_123")

            assert conn.provider == OpenFinanceProvider.ESUN_BANK
            assert conn.status == ConnectionStatus.ACTIVE
            assert conn.institution_name == "E.Sun Bank"
            assert conn.institution_id == "ESUN"
            assert len(conn.account_ids) == 2

    @pytest.mark.asyncio
    async def test_connect_without_api_key_raises(self, adapter):
        """Should raise error if API key not configured."""
        adapter.api_key = None
        with pytest.raises(ProviderAuthenticationError, match="API key not configured"):
            await adapter.connect(uuid4(), "auth_code")

    @pytest.mark.asyncio
    async def test_connect_invalid_credentials(self, adapter):
        """Should raise authentication error on 401."""
        with patch.object(adapter.client, "post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock(status_code=401)
            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(side_effect=Exception("401")),
                status_code=401,
            )
            # httpx raises HTTPStatusError
            from httpx import HTTPStatusError
            mock_post.side_effect = HTTPStatusError(
                "401",
                request=MagicMock(),
                response=mock_response,
            )

            with pytest.raises(ProviderConnectionError):
                await adapter.connect(uuid4(), "invalid_code")

    @pytest.mark.asyncio
    async def test_sync_accounts_returns_balances(self, adapter):
        """Should return normalized account balances."""
        connection = OpenFinanceConnection(
            id=uuid4(),
            user_id=uuid4(),
            provider=OpenFinanceProvider.ESUN_BANK,
            status=ConnectionStatus.ACTIVE,
            institution_name="E.Sun Bank",
            institution_id="ESUN",
            account_ids=["acc1"],
            permissions=["READ_BALANCES"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data = {
            "account_type": "CHECKING",
            "account_name": "My Checking",
            "balance": 50000.0,
            "currency": "TWD",
        }

        with patch.object(adapter.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=mock_data),
            )

            accounts = await adapter.sync_accounts(connection)

            assert len(accounts) == 1
            assert accounts[0].account_type == "checking"
            assert accounts[0].balance == 50000.0
            assert accounts[0].currency == "TWD"

    @pytest.mark.asyncio
    async def test_sync_holdings_returns_assets(self, adapter):
        """Should return normalized holdings."""
        connection = OpenFinanceConnection(
            id=uuid4(),
            user_id=uuid4(),
            provider=OpenFinanceProvider.ESUN_BANK,
            status=ConnectionStatus.ACTIVE,
            institution_name="E.Sun Bank",
            institution_id="ESUN",
            account_ids=["acc1"],
            permissions=["READ_HOLDINGS"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_data = {
            "holdings": [
                {
                    "symbol": "2330",
                    "name": "TSMC",
                    "quantity": 100,
                    "market_value": 15000,
                    "cost_basis": 12000,
                    "unrealized_gain": 3000,
                    "unrealized_gain_percent": 25.0,
                }
            ]
        }

        with patch.object(adapter.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=mock_data),
            )

            holdings = await adapter.sync_holdings(connection)

            assert len(holdings) == 1
            assert holdings[0].symbol == "2330"
            assert holdings[0].quantity == 100
            assert holdings[0].asset_class == "stock"

    @pytest.mark.asyncio
    async def test_disconnect_returns_true(self, adapter):
        """Should return True on successful disconnect."""
        connection = OpenFinanceConnection(
            id=uuid4(),
            user_id=uuid4(),
            provider=OpenFinanceProvider.ESUN_BANK,
            status=ConnectionStatus.ACTIVE,
            institution_name="E.Sun Bank",
            institution_id="ESUN",
            account_ids=["acc1"],
            permissions=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with patch.object(adapter.client, "delete", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = MagicMock(raise_for_status=MagicMock())
            result = await adapter.disconnect(connection)
            assert result is True

    def test_normalize_account_type(self, adapter):
        """Should normalize E.Sun account types to standard types."""
        assert adapter._normalize_account_type("CHECKING") == "checking"
        assert adapter._normalize_account_type("SAVINGS") == "savings"
        assert adapter._normalize_account_type("INVESTMENT") == "investment"
        assert adapter._normalize_account_type("CREDIT") == "credit"
        assert adapter._normalize_account_type("LOAN") == "loan"
        assert adapter._normalize_account_type("UNKNOWN") == "other"

    def test_classify_asset_taiwan_stocks(self, adapter):
        """Should classify Taiwan stock codes correctly."""
        assert adapter._classify_asset("2330") == "stock"
        assert adapter._classify_asset("2317") == "stock"
        assert adapter._classify_asset("2454") == "stock"

    def test_classify_asset_index(self, adapter):
        """Should classify indices correctly."""
        assert adapter._classify_asset("^TWII") == "stock"
        assert adapter._classify_asset("00") == "stock"


class TestYodleeAdapter:
    """Tests for Yodlee adapter."""

    @pytest.fixture
    def adapter(self):
        """Create Yodlee adapter with mock credentials."""
        return YodleeAdapter(api_key="test_key", api_secret="test_secret")

    @pytest.mark.asyncio
    async def test_get_access_token_success(self, adapter):
        """Should obtain access token via client credentials."""
        mock_response = {"token": {"accessToken": "yodlee_token_123"}}

        with patch.object(adapter.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=mock_response),
            )

            token = await adapter._get_access_token()
            assert token == "yodlee_token_123"

    @pytest.mark.asyncio
    async def test_get_access_token_no_credentials(self):
        """Should raise error if credentials not configured."""
        adapter = YodleeAdapter(api_key=None, api_secret=None)
        with pytest.raises(ProviderAuthenticationError, match="credentials not configured"):
            await adapter._get_access_token()

    @pytest.mark.asyncio
    async def test_sync_accounts_normalizes_data(self, adapter):
        """Should normalize Yodlee account data."""
        connection = OpenFinanceConnection(
            id=uuid4(),
            user_id=uuid4(),
            provider=OpenFinanceProvider.YODLEE,
            status=ConnectionStatus.ACTIVE,
            institution_name="Yodlee Bank",
            institution_id="YODLEE",
            account_ids=["12345"],
            permissions=["READ_BALANCES"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_response = {
            "account": [
                {
                    "id": "12345",
                    "accountName": "Checking Account",
                    "accountType": "CHECKING",
                    "balance": {"amount": 10000, "currency": "USD"},
                    "providerName": "Bank of America",
                }
            ]
        }

        with patch.object(adapter, "_get_access_token", new_callable=AsyncMock) as mock_token:
            mock_token.return_value = "test_token"
            with patch.object(adapter.client, "get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = MagicMock(
                    raise_for_status=MagicMock(),
                    json=MagicMock(return_value=mock_response),
                )

                accounts = await adapter.sync_accounts(connection)

                assert len(accounts) == 1
                assert accounts[0].account_type == "checking"
                assert accounts[0].balance == 10000.0
                assert accounts[0].provider == OpenFinanceProvider.YODLEE

    def test_normalize_account_type(self, adapter):
        """Should normalize Yodlee account types."""
        assert adapter._normalize_account_type("CHECKING") == "checking"
        assert adapter._normalize_account_type("SAVINGS") == "savings"
        assert adapter._normalize_account_type("INVESTMENT") == "investment"
        assert adapter._normalize_account_type("BROKERAGE_MARGIN") == "investment"
        assert adapter._normalize_account_type("CREDIT_CARD") == "credit"
        assert adapter._normalize_account_type("LOAN") == "loan"

    def test_classify_asset(self, adapter):
        """Should classify Yodlee security types."""
        assert adapter._classify_asset("EQUITY") == "stock"
        assert adapter._classify_asset("ETF") == "stock"
        assert adapter._classify_asset("MUTUAL_FUND") == "stock"
        assert adapter._classify_asset("BOND") == "bond"
        assert adapter._classify_asset("CASH") == "cash"


class TestPlaidAdapter:
    """Tests for Plaid adapter."""

    @pytest.fixture
    def adapter(self):
        """Create Plaid adapter with mock credentials."""
        return PlaidAdapter(client_id="test_client", secret="test_secret")

    @pytest.mark.asyncio
    async def test_connect_exchanges_token(self, adapter):
        """Should exchange public token for access token."""
        user_id = uuid4()
        mock_response = {
            "access_token": "access_plaid_123",
            "item_id": "item_abc",
        }

        with patch.object(adapter.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=mock_response),
            )

            conn = await adapter.connect(user_id, "public_token_xyz")

            assert conn.provider == OpenFinanceProvider.PLAID
            assert conn.status == ConnectionStatus.ACTIVE
            assert conn.institution_id == "item_abc"

    @pytest.mark.asyncio
    async def test_connect_without_credentials_raises(self, adapter):
        """Should raise error if Plaid credentials not configured."""
        adapter.api_key = None
        adapter.api_secret = None
        with pytest.raises(ProviderAuthenticationError, match="credentials not configured"):
            await adapter.connect(uuid4(), "public_token")

    @pytest.mark.asyncio
    async def test_sync_accounts_normalizes_data(self, adapter):
        """Should normalize Plaid account data."""
        connection = OpenFinanceConnection(
            id=uuid4(),
            user_id=uuid4(),
            provider=OpenFinanceProvider.PLAID,
            status=ConnectionStatus.ACTIVE,
            institution_name="Chase",
            institution_id="item_123",
            account_ids=["acc_123"],
            permissions=["READ_BALANCES"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_response = {
            "accounts": [
                {
                    "account_id": "acc_123",
                    "name": "Checking",
                    "type": "depository",
                    "balances": {"current": 5000, "iso_currency_code": "USD"},
                }
            ],
            "item": {"institution_name": "Chase"},
        }

        with patch.object(adapter.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=mock_response),
            )

            accounts = await adapter.sync_accounts(connection)

            assert len(accounts) == 1
            assert accounts[0].account_type == "checking"
            assert accounts[0].balance == 5000.0

    @pytest.mark.asyncio
    async def test_sync_holdings_with_security_lookup(self, adapter):
        """Should properly look up security details for holdings."""
        connection = OpenFinanceConnection(
            id=uuid4(),
            user_id=uuid4(),
            provider=OpenFinanceProvider.PLAID,
            status=ConnectionStatus.ACTIVE,
            institution_name="Vanguard",
            institution_id="item_456",
            account_ids=["acc_456"],
            permissions=["READ_HOLDINGS"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_response = {
            "holdings": [
                {
                    "security_id": "sec_001",
                    "account_id": "acc_456",
                    "quantity": 50,
                    "market_value": 25000,
                    "cost_basis": 20000,
                    "institution_value": 25000,
                }
            ],
            "securities": [
                {
                    "security_id": "sec_001",
                    "ticker_symbol": "VTI",
                    "name": "Vanguard Total Stock Market ETF",
                    "type": "etf",
                }
            ],
        }

        with patch.object(adapter.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = MagicMock(
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=mock_response),
            )

            holdings = await adapter.sync_holdings(connection)

            assert len(holdings) == 1
            assert holdings[0].symbol == "VTI"
            assert holdings[0].quantity == 50
            assert holdings[0].current_value == 25000

    def test_normalize_account_type(self, adapter):
        """Should normalize Plaid account types."""
        assert adapter._normalize_account_type("depository") == "checking"
        assert adapter._normalize_account_type("investment") == "investment"
        assert adapter._normalize_account_type("credit") == "credit"
        assert adapter._normalize_account_type("loan") == "loan"

    def test_classify_asset(self, adapter):
        """Should classify Plaid security types."""
        assert adapter._classify_asset("equity") == "stock"
        assert adapter._classify_asset("etf") == "stock"
        assert adapter._classify_asset("bond") == "bond"
        assert adapter._classify_asset("cash") == "cash"
        assert adapter._classify_asset("cryptocurrency") == "crypto"


class TestBuildProfile:
    """Tests for building comprehensive financial profiles."""

    @pytest.mark.asyncio
    async def test_build_profile_aggregates_all_connections(self):
        """Should aggregate data from multiple connections."""
        adapter = ESunBankAdapter(api_key="test_key")

        connection = OpenFinanceConnection(
            id=uuid4(),
            user_id=uuid4(),
            provider=OpenFinanceProvider.ESUN_BANK,
            status=ConnectionStatus.ACTIVE,
            institution_name="E.Sun Bank",
            institution_id="ESUN",
            account_ids=["acc1"],
            permissions=["READ_BALANCES", "READ_HOLDINGS"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with patch.object(adapter, "sync_accounts", new_callable=AsyncMock) as mock_sync:
            mock_sync.return_value = [
                AccountBalance(
                    account_id="acc1",
                    account_name="Checking",
                    account_type="checking",
                    balance=50000,
                    currency="TWD",
                    provider=OpenFinanceProvider.ESUN_BANK,
                    institution_name="E.Sun Bank",
                    last_updated=datetime.now(),
                )
            ]
            with patch.object(adapter, "sync_holdings", new_callable=AsyncMock) as mock_holdings:
                mock_holdings.return_value = [
                    HoldingAsset(
                        symbol="2330",
                        name="TSMC",
                        quantity=100,
                        current_value=15000,
                        cost_basis=12000,
                    )
                ]

                profile = await adapter.build_profile(uuid4(), [connection])

                assert profile.total_cash == 50000
                assert profile.total_investments == 0
                assert len(profile.accounts) == 1
                assert len(profile.holdings) == 1

    @pytest.mark.asyncio
    async def test_build_profile_skips_inactive_connections(self):
        """Should skip connections that are not ACTIVE."""
        adapter = ESunBankAdapter(api_key="test_key")

        inactive_connection = OpenFinanceConnection(
            id=uuid4(),
            user_id=uuid4(),
            provider=OpenFinanceProvider.ESUN_BANK,
            status=ConnectionStatus.INACTIVE,
            institution_name="E.Sun Bank",
            institution_id="ESUN",
            account_ids=["acc1"],
            permissions=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        profile = await adapter.build_profile(uuid4(), [inactive_connection])

        # Should return empty profile for inactive connection
        assert profile.total_assets == 0
        assert len(profile.accounts) == 0
        assert len(profile.holdings) == 0

    @pytest.mark.asyncio
    async def test_build_profile_calculates_totals(self):
        """Should correctly calculate total assets, liabilities, etc."""
        adapter = ESunBankAdapter(api_key="test_key")

        connection = OpenFinanceConnection(
            id=uuid4(),
            user_id=uuid4(),
            provider=OpenFinanceProvider.ESUN_BANK,
            status=ConnectionStatus.ACTIVE,
            institution_name="E.Sun Bank",
            institution_id="ESUN",
            account_ids=["checking", "credit_card"],
            permissions=["READ_BALANCES"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        async def mock_sync_accounts(conn):
            if "checking" in conn.account_ids:
                return [
                    AccountBalance(
                        account_id="checking",
                        account_name="Checking",
                        account_type="checking",
                        balance=100000,
                        currency="TWD",
                        provider=OpenFinanceProvider.ESUN_BANK,
                        institution_name="E.Sun Bank",
                        last_updated=datetime.now(),
                    ),
                    AccountBalance(
                        account_id="credit_card",
                        account_name="Credit Card",
                        account_type="credit",
                        balance=-20000,  # Negative = liability
                        currency="TWD",
                        provider=OpenFinanceProvider.ESUN_BANK,
                        institution_name="E.Sun Bank",
                        last_updated=datetime.now(),
                    ),
                ]
            return []

        with patch.object(adapter, "sync_accounts", side_effect=mock_sync_accounts):
            with patch.object(adapter, "sync_holdings", new_callable=AsyncMock) as mock_holdings:
                mock_holdings.return_value = []
                profile = await adapter.build_profile(uuid4(), [connection])

                assert profile.total_assets == 100000
                assert profile.total_liabilities == 20000
                assert profile.total_net_worth == 80000
                assert profile.total_debt == 20000

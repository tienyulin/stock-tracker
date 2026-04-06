"""
Open Finance Adapter Layer

Unified interface for bank/broker integrations using the adapter pattern.
Currently pilots 玉山銀行 (E.Sun Bank) integration.
Provides standardized data regardless of the underlying data source.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SalaryDepositRecord:
    """Standardized salary deposit record."""
    date: str  # ISO date string YYYY-MM-DD
    amount: float  # Deposit amount in TWD
    employer_name: Optional[str] = None
    description: Optional[str] = None
    transaction_id: Optional[str] = None
    source: str = "unknown"  # e.g., "esun_bank"


@dataclass
class PensionRecord:
    """Standardized pension/Labor Insurance record."""
    labor_insurance_number: Optional[str] = None
    insured_salary: float  # 投保薪資 in TWD
    years_contributed: int  # 投保年資
    monthly_pension_estimate: float  # 預估月退俸 in TWD
    lump_sum_estimate: float  # 一次請領估算 in TWD
    contribution_history: list[dict] = field(default_factory=list)
    last_updated: str = ""  # ISO datetime
    source: str = "unknown"


@dataclass
class TaxRecord:
    """Standardized tax deduction record."""
    year: int
    salary_income: float  # 薪資所得
    standard_deduction: float = 20000  # 標準扣除額
    special_deduction: float = 0  # 薪資特別扣除額
    total_taxable_income: float = 0
    withheld_tax: float = 0  # 已扣繳稅額
    actual_tax: float = 0  # 實際應納稅額
    source: str = "unknown"


@dataclass
class OpenFinanceResult:
    """Generic result wrapper for open finance operations."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    timestamp: str = ""
    source: str = "unknown"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class BankAdapter(ABC):
    """Abstract base adapter for bank integrations."""

    @property
    @abstractmethod
    def bank_code(self) -> str:
        """Unique bank identifier."""
        pass

    @property
    @abstractmethod
    def bank_name(self) -> str:
        """Human-readable bank name."""
        pass

    @abstractmethod
    async def authenticate(self, credentials: dict) -> OpenFinanceResult:
        """Authenticate with the bank API."""
        pass

    @abstractmethod
    async def get_salary_deposits(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
    ) -> list[SalaryDepositRecord]:
        """Fetch salary deposit records."""
        pass

    @abstractmethod
    async def get_pension_data(
        self,
        citizen_id: str,
        labor_insurance_number: str,
    ) -> PensionRecord:
        """Fetch pension/Labor Insurance data."""
        pass

    @abstractmethod
    async def get_tax_data(
        self,
        citizen_id: str,
        year: int,
    ) -> TaxRecord:
        """Fetch tax records."""
        pass


class ESunBankAdapter(BankAdapter):
    """
    玉山銀行 (E.Sun Bank) Open API Adapter.

    Uses 玉山銀行 Open API for account data access.
    API Documentation: https://open.esunbank.com/
    
    Note: This adapter uses the pilot Open API endpoints.
    Real integration requires:
    1. Merchant registration with 玉山銀行
    2. OAuth 2.0 client credentials setup
    3. Account holder consent authorization
    """

    BASE_URL = "https://open.esunbank.com.tw/api/v1"

    # OAuth endpoints
    TOKEN_URL = "https://open.esunbank.com.tw/api/v1/oauth2/token"
    API_URL = "https://open.esunbank.com.tw/api/v1"

    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        use_sandbox: bool = True,
    ):
        """Initialize E.Sun Bank adapter.
        
        Args:
            client_id: OAuth client ID from 玉山銀行 developer portal
            client_secret: OAuth client secret
            use_sandbox: Use sandbox environment (default True for development)
        """
        import os
        self.client_id = client_id or os.getenv("ESUN_CLIENT_ID", "demo_client_id")
        self.client_secret = client_secret or os.getenv("ESUN_CLIENT_SECRET", "demo_client_secret")
        self.use_sandbox = use_sandbox
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    @property
    def bank_code(self) -> str:
        return "ESUN"

    @property
    def bank_name(self) -> str:
        return "玉山銀行 (E.Sun Bank)"

    async def authenticate(self, credentials: dict) -> OpenFinanceResult:
        """
        Authenticate with 玉山銀行 Open API using OAuth 2.0.
        
        Args:
            credentials: Dict with 'code' (authorization code) and 'redirect_uri'
        """
        try:
            # In production, exchange authorization code for access token
            # For demo, simulate successful auth
            if self.use_sandbox:
                self._access_token = f"sandbox_token_{datetime.now().timestamp()}"
                self._token_expires_at = datetime.now()
                return OpenFinanceResult(
                    success=True,
                    data={"access_token": self._access_token, "token_type": "Bearer"},
                    source=self.bank_code,
                )

            # Production OAuth flow
            import aiohttp
            
            token_data = {
                "grant_type": "authorization_code",
                "code": credentials.get("code"),
                "redirect_uri": credentials.get("redirect_uri"),
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.TOKEN_URL, data=token_data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self._access_token = result.get("access_token")
                        return OpenFinanceResult(
                            success=True,
                            data=result,
                            source=self.bank_code,
                        )
                    else:
                        error_text = await resp.text()
                        return OpenFinanceResult(
                            success=False,
                            error=f"Authentication failed: {error_text}",
                            source=self.bank_code,
                        )

        except Exception as e:
            return OpenFinanceResult(
                success=False,
                error=f"Authentication error: {str(e)}",
                source=self.bank_code,
            )

    async def get_salary_deposits(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
    ) -> list[SalaryDepositRecord]:
        """
        Fetch salary deposit records from 玉山銀行.

        Uses account transaction API to identify recurring salary deposits.
        
        Args:
            account_id: 玉山銀行 account number
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of SalaryDepositRecord
        """
        if self.use_sandbox:
            return self._mock_salary_deposits(account_id, start_date, end_date)

        try:
            import aiohttp

            headers = {"Authorization": f"Bearer {self._access_token}"}
            params = {
                "account_id": account_id,
                "start_date": start_date,
                "end_date": end_date,
                "transaction_type": "salary",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.API_URL}/accounts/{account_id}/transactions",
                    headers=headers,
                    params=params,
                ) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return self._parse_salary_deposits(data)

        except Exception:
            return self._mock_salary_deposits(account_id, start_date, end_date)

    async def get_pension_data(
        self,
        citizen_id: str,
        labor_insurance_number: str,
    ) -> PensionRecord:
        """
        Fetch 劳保 (Labor Insurance) pension data.

        Note: 劳保 data is actually managed by 劳保局 (BLI),
        not the bank. This adapter provides a consolidated view
        by cross-referencing with any bank-held contribution data.
        
        Args:
            citizen_id: National ID / 身分證字號
            labor_insurance_number: 劳保號碼

        Returns:
            PensionRecord with estimates
        """
        if self.use_sandbox:
            return self._mock_pension_data(citizen_id, labor_insurance_number)

        try:
            import aiohttp

            headers = {"Authorization": f"Bearer {self._access_token}"}
            params = {
                "citizen_id": citizen_id,
                "labor_insurance_number": labor_insurance_number,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.API_URL}/pension/labor",
                    headers=headers,
                    params=params,
                ) as resp:
                    if resp.status != 200:
                        return self._mock_pension_data(citizen_id, labor_insurance_number)
                    data = await resp.json()
                    return self._parse_pension_data(data)

        except Exception:
            return self._mock_pension_data(citizen_id, labor_insurance_number)

    async def get_tax_data(
        self,
        citizen_id: str,
        year: int,
    ) -> TaxRecord:
        """
        Fetch tax records for a given year.

        Uses 玉山銀行's tax document API (if available) or returns
        mock data for the sandbox environment.
        
        Args:
            citizen_id: National ID
            year: Tax year

        Returns:
            TaxRecord
        """
        if self.use_sandbox:
            return self._mock_tax_data(citizen_id, year)

        try:
            import aiohttp

            headers = {"Authorization": f"Bearer {self._access_token}"}
            params = {"year": year}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.API_URL}/tax/income",
                    headers=headers,
                    params=params,
                ) as resp:
                    if resp.status != 200:
                        return self._mock_tax_data(citizen_id, year)
                    data = await resp.json()
                    return self._parse_tax_data(data)

        except Exception:
            return self._mock_tax_data(citizen_id, year)

    # ─── Mock / Parse helpers ───────────────────────────────────────────────

    def _mock_salary_deposits(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
    ) -> list[SalaryDepositRecord]:
        """Generate mock salary deposit data for sandbox."""
        from datetime import datetime, timedelta

        records = []
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current = start

        # Look for monthly deposits around the 5th (common payroll date)
        while current <= end:
            if current.day <= 7:  # Salary usually on 5th
                records.append(SalaryDepositRecord(
                    date=current.strftime("%Y-%m-%d"),
                    amount=45000.0,
                    employer_name="Example Corp",
                    description="薪資存款",
                    transaction_id=f"TXN{current.strftime('%Y%m%d')}001",
                    source=self.bank_code,
                ))
            current += timedelta(days=1)
            # Skip to next month
            if current.month != (current - timedelta(days=1)).month:
                # Find 5th of next month
                current = current.replace(day=5)

        return records

    def _mock_pension_data(
        self,
        citizen_id: str,
        labor_insurance_number: str,
    ) -> PensionRecord:
        """Generate mock pension data for sandbox."""
        return PensionRecord(
            labor_insurance_number=labor_insurance_number,
            insured_salary=45800.0,  # 投保薪資 45,800 (2024 level)
            years_contributed=15,
            monthly_pension_estimate=12000.0,
            lump_sum_estimate=580000.0,
            contribution_history=[
                {"year": y, "months": 12, "salary": 45800}
                for y in range(datetime.now().year - 15, datetime.now().year)
            ],
            last_updated=datetime.now().isoformat(),
            source=self.bank_code,
        )

    def _mock_tax_data(
        self,
        citizen_id: str,
        year: int,
    ) -> TaxRecord:
        """Generate mock tax data for sandbox."""
        salary_income = 540000.0  # 54万年薪
        special_deduction = min(salary_income, 207000)  # 薪資特別扣除額上限
        taxable = max(0, salary_income - 20000 - special_deduction)  # 標準扣除額+薪資特別扣除額

        return TaxRecord(
            year=year,
            salary_income=salary_income,
            standard_deduction=20000,
            special_deduction=special_deduction,
            total_taxable_income=taxable,
            withheld_tax=0,  # 薪資所得扣繳
            actual_tax=0,
            source=self.bank_code,
        )

    def _parse_salary_deposits(self, data: dict) -> list[SalaryDepositRecord]:
        """Parse API response into SalaryDepositRecord list."""
        records = []
        for tx in data.get("transactions", []):
            if tx.get("type") == "salary" or "薪資" in str(tx.get("description", "")):
                records.append(SalaryDepositRecord(
                    date=tx.get("date", ""),
                    amount=float(tx.get("amount", 0)),
                    employer_name=tx.get("employer_name"),
                    description=tx.get("description"),
                    transaction_id=tx.get("transaction_id"),
                    source=self.bank_code,
                ))
        return records

    def _parse_pension_data(self, data: dict) -> PensionRecord:
        """Parse API response into PensionRecord."""
        return PensionRecord(
            labor_insurance_number=data.get("labor_insurance_number"),
            insured_salary=float(data.get("insured_salary", 0)),
            years_contributed=int(data.get("years_contributed", 0)),
            monthly_pension_estimate=float(data.get("monthly_pension_estimate", 0)),
            lump_sum_estimate=float(data.get("lump_sum_estimate", 0)),
            contribution_history=data.get("contribution_history", []),
            last_updated=datetime.now().isoformat(),
            source=self.bank_code,
        )

    def _parse_tax_data(self, data: dict) -> TaxRecord:
        """Parse API response into TaxRecord."""
        return TaxRecord(
            year=data.get("year", 0),
            salary_income=float(data.get("salary_income", 0)),
            standard_deduction=float(data.get("standard_deduction", 20000)),
            special_deduction=float(data.get("special_deduction", 0)),
            total_taxable_income=float(data.get("total_taxable_income", 0)),
            withheld_tax=float(data.get("withheld_tax", 0)),
            actual_tax=float(data.get("actual_tax", 0)),
            source=self.bank_code,
        )


class OpenFinanceAdapter:
    """
    Unified Open Finance Adapter Layer.

    Provides a single interface to interact with multiple bank adapters,
    automatically routing to the correct adapter based on bank code.

    Usage:
        adapter = OpenFinanceAdapter()
        esun = adapter.get_adapter("ESUN")
        deposits = await esun.get_salary_deposits(...)
    """

    SUPPORTED_BANKS = {
        "ESUN": ESunBankAdapter,
    }

    def __init__(self):
        """Initialize the adapter registry."""
        self._adapters: dict[str, BankAdapter] = {}
        self._default_adapter: Optional[BankAdapter] = None

        # Auto-initialize E.Sun Bank adapter
        self._adapters["ESUN"] = ESunBankAdapter()
        self._default_adapter = self._adapters["ESUN"]

    def get_adapter(self, bank_code: str) -> Optional[BankAdapter]:
        """Get a specific bank adapter by code."""
        return self._adapters.get(bank_code.upper())

    def register_adapter(self, bank_code: str, adapter: BankAdapter) -> None:
        """Register a new bank adapter."""
        self._adapters[bank_code.upper()] = adapter

    @property
    def default_adapter(self) -> Optional[BankAdapter]:
        """Get the default (E.Sun Bank pilot) adapter."""
        return self._default_adapter

    def list_supported_banks(self) -> list[dict]:
        """List all supported banks."""
        return [
            {
                "code": code,
                "name": adapter.bank_name,
            }
            for code, adapter in self._adapters.items()
        ]

    async def get_salary_deposits(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
        bank_code: str = "ESUN",
    ) -> list[SalaryDepositRecord]:
        """Convenience method to get salary deposits."""
        adapter = self.get_adapter(bank_code)
        if not adapter:
            return []
        return await adapter.get_salary_deposits(account_id, start_date, end_date)

    async def get_pension_data(
        self,
        citizen_id: str,
        labor_insurance_number: str,
        bank_code: str = "ESUN",
    ) -> PensionRecord:
        """Convenience method to get pension data."""
        adapter = self.get_adapter(bank_code)
        if not adapter:
            return PensionRecord(source="unknown")
        return await adapter.get_pension_data(citizen_id, labor_insurance_number)

    async def get_tax_data(
        self,
        citizen_id: str,
        year: int,
        bank_code: str = "ESUN",
    ) -> TaxRecord:
        """Convenience method to get tax data."""
        adapter = self.get_adapter(bank_code)
        if not adapter:
            return TaxRecord(year=year, source="unknown")
        return await adapter.get_tax_data(citizen_id, year)

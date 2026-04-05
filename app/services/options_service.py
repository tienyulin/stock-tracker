"""
Options Service

Provides options data retrieval and Greek letters calculation.
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx


@dataclass
class GreekLetters:
    """Greek letters for an option."""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


@dataclass
class OptionQuote:
    """Option quote data."""
    symbol: str
    strike: float
    expiry: str
    option_type: str  # "call" or "put"
    last_price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    implied_volatility: float
    intrinsic_value: float
    moneyness: str  # "itm", "atm", "otm"


@dataclass
class OptionsChain:
    """Full options chain for a symbol."""
    symbol: str
    underlying_price: float
    timestamp: int
    calls: list[OptionQuote]
    puts: list[OptionQuote]


class OptionsService:
    """Service for options data and Greek calculations."""

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": "Mozilla/5.0 (compatible; StockTracker/1.0)"},
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_options_chain(
        self, symbol: str, expiry: Optional[str] = None
    ) -> OptionsChain:
        """
        Fetch options chain for a symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL", "2330.TW")
            expiry: Specific expiry date (YYYY-MM-DD), or None for nearest

        Returns:
            OptionsChain with calls and puts
        """
        client = await self._get_client()

        # First get the underlying price
        quote_url = f"{self.BASE_URL}/chart/{symbol}"
        quote_params = {"interval": "1d", "range": "1d"}
        quote_resp = await client.get(quote_url, params=quote_params)
        quote_resp.raise_for_status()
        quote_data = quote_resp.json()
        meta = quote_data.get("chart", {}).get("result", [{}])[0].get("meta", {})
        underlying_price = meta.get("regularMarketPrice", 0)

        # Get options dates if not specified
        if expiry is None:
            expiry_url = f"{self.BASE_URL}/options/{symbol}"
            resp = await client.get(expiry_url)
            resp.raise_for_status()
            expiry_data = resp.json()
            expirations = expiry_data.get("optionChain", {}).get("result", [{}])[0].get("expirationDates", [])
            if not expirations:
                raise ValueError(f"No options available for {symbol}")
            # Use nearest expiry (index 0)
            expiry_ts = expirations[0]
            expiry = datetime.utcfromtimestamp(expiry_ts).strftime("%Y-%m-%d")

        # Fetch options chain for specific expiry
        options_url = f"{self.BASE_URL}/options/{symbol}"
        options_params = {"date": expiry}
        resp = await client.get(options_url, params=options_params)
        resp.raise_for_status()
        data = resp.json()

        result = data.get("optionChain", {}).get("result", [{}])[0]
        options = result.get("options", [{}])[0]
        calls_data = options.get("calls", [])
        puts_data = options.get("puts", [])

        timestamp = int(datetime.utcnow().timestamp())

        calls = [
            OptionQuote(
                symbol=symbol,
                strike=c.get("strike", 0),
                expiry=expiry,
                option_type="call",
                last_price=c.get("lastPrice", 0),
                bid=c.get("bid", 0),
                ask=c.get("ask", 0),
                volume=c.get("volume", 0),
                open_interest=c.get("openInterest", 0),
                implied_volatility=c.get("impliedVolatility", 0) * 100
                if c.get("impliedVolatility") is not None
                else 0,
                intrinsic_value=max(0, underlying_price - c.get("strike", 0))
                if c.get("inTheMoney", False)
                else 0,
                moneyness=self._get_moneyness(underlying_price, c.get("strike", 0), "call"),
            )
            for c in calls_data
        ]

        puts = [
            OptionQuote(
                symbol=symbol,
                strike=p.get("strike", 0),
                expiry=expiry,
                option_type="put",
                last_price=p.get("lastPrice", 0),
                bid=p.get("bid", 0),
                ask=p.get("ask", 0),
                volume=p.get("volume", 0),
                open_interest=p.get("openInterest", 0),
                implied_volatility=p.get("impliedVolatility", 0) * 100
                if p.get("impliedVolatility") is not None
                else 0,
                intrinsic_value=max(0, p.get("strike", 0) - underlying_price)
                if p.get("inTheMoney", False)
                else 0,
                moneyness=self._get_moneyness(underlying_price, p.get("strike", 0), "put"),
            )
            for p in puts_data
        ]

        return OptionsChain(
            symbol=symbol,
            underlying_price=underlying_price,
            timestamp=timestamp,
            calls=calls,
            puts=puts,
        )

    def _get_moneyness(self, spot: float, strike: float, option_type: str) -> str:
        """Determine moneyness of an option."""
        if option_type == "call":
            if strike < spot * 0.98:
                return "itm"
            elif strike > spot * 1.02:
                return "otm"
            else:
                return "atm"
        else:
            if strike > spot * 1.02:
                return "itm"
            elif strike < spot * 0.98:
                return "otm"
            else:
                return "atm"

    async def calculate_greeks(
        self,
        symbol: str,
        strike: float,
        expiry: str,
        option_type: str,
        spot_price: Optional[float] = None,
        risk_free_rate: float = 0.045,
    ) -> GreekLetters:
        """
        Calculate Greek letters for an option using Black-Scholes.

        Args:
            symbol: Underlying symbol
            strike: Strike price
            expiry: Expiry date (YYYY-MM-DD)
            option_type: "call" or "put"
            spot_price: Current spot price (fetched if not provided)
            risk_free_rate: Risk-free interest rate (default 4.5%)

        Returns:
            GreekLetters with delta, gamma, theta, vega, rho
        """
        if spot_price is None:
            client = await self._get_client()
            quote_url = f"{self.BASE_URL}/chart/{symbol}"
            resp = await client.get(
                quote_url, params={"interval": "1d", "range": "1d"}
            )
            resp.raise_for_status()
            data = resp.json()
            spot_price = data.get("chart", {}).get("result", [{}])[0].get(
                "meta", {}
            ).get("regularMarketPrice", 0)

        # Get IV from options chain
        chain = await self.get_options_chain(symbol, expiry)
        iv = 0.20  # default 20% if not found
        for opt in chain.calls + chain.puts:
            if abs(opt.strike - strike) < 0.01 and opt.option_type == option_type:
                iv = opt.implied_volatility / 100
                break

        # Time to expiry in years
        expiry_dt = datetime.strptime(expiry, "%Y-%m-%d")
        now = datetime.utcnow()
        T = max((expiry_dt - now).days / 365.0, 0.001)

        d1 = self._d1(spot_price, strike, T, risk_free_rate, iv)
        d2 = d1 - iv * math.sqrt(T)

        if option_type == "call":
            delta = self._delta_call(d1)
            rho = self._rho_call(strike, T, risk_free_rate, d2)
        else:
            delta = self._delta_put(d1)
            rho = self._rho_put(strike, T, risk_free_rate, d2)

        gamma = self._gamma(iv, spot_price, strike, T)
        theta = self._theta(iv, spot_price, strike, T, d1, option_type)
        vega = self._vega(iv, spot_price, T)

        return GreekLetters(
            delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho
        )

    def _d1(
        self, S: float, K: float, T: float, r: float, sigma: float
    ) -> float:
        """Calculate d1 in Black-Scholes."""
        if T <= 0 or sigma <= 0:
            return 0
        return (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))

    def _norm_cdf(self, x: float) -> float:
        """Standard normal cumulative distribution function."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _norm_pdf(self, x: float) -> float:
        """Standard normal probability density function."""
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

    def _delta_call(self, d1: float) -> float:
        return self._norm_cdf(d1)

    def _delta_put(self, d1: float) -> float:
        return self._norm_cdf(d1) - 1

    def _gamma(self, sigma: float, S: float, K: float, T: float) -> float:
        if T <= 0 or sigma <= 0:
            return 0
        return self._norm_pdf(self._d1(S, K, T, 0, sigma)) / (S * sigma * math.sqrt(T))

    def _theta(
        self, sigma: float, S: float, K: float, T: float, d1: float, option_type: str
    ) -> float:
        if T <= 0 or sigma <= 0:
            return 0
        term1 = -(S * sigma * self._norm_pdf(d1)) / (2 * math.sqrt(T))
        term2 = 0.0
        if option_type == "call":
            term2 = 0.045 * K * math.exp(-0.045 * T) * self._norm_cdf(d1 - sigma * math.sqrt(T))
        else:
            term2 = -0.045 * K * math.exp(-0.045 * T) * self._norm_cdf(-d1 + sigma * math.sqrt(T))
        return (term1 - term2) / 365  # per day

    def _vega(self, sigma: float, S: float, T: float) -> float:
        if T <= 0 or sigma <= 0:
            return 0
        return S * self._norm_pdf(self._d1(S, 0, T, 0, sigma)) * math.sqrt(T) / 100

    def _rho_call(self, K: float, T: float, r: float, d2: float) -> float:
        if T <= 0:
            return 0
        return K * T * math.exp(-r * T) * self._norm_cdf(d2) / 100

    def _rho_put(self, K: float, T: float, r: float, d2: float) -> float:
        if T <= 0:
            return 0
        return -K * T * math.exp(-r * T) * self._norm_cdf(-d2) / 100

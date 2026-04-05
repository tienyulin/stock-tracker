"""
Options Service — Greek Letters & Options Data
"""

import asyncio
import math
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Literal

import httpx
from scipy.stats import norm

from app.exceptions import SymbolNotFoundError, NetworkError, RateLimitError, ValidationError


# --- Black-Scholes Greek Letters ---

def _d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Calculate d1 in Black-Scholes."""
    if T <= 0 or sigma <= 0:
        return 0.0
    return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))


def _d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Calculate d2 in Black-Scholes."""
    if T <= 0 or sigma <= 0:
        return 0.0
    return _d1(S, K, T, r, sigma) - sigma * math.sqrt(T)


def calc_delta(S: float, K: float, T: float, r: float, sigma: float, option_type: Literal["CALL", "PUT"]) -> float:
    """Calculate Delta."""
    if T <= 0:
        if option_type == "CALL":
            if S > K:
                return 1.0
            elif S < K:
                return 0.0
            else:
                return 0.5  # S == K, ATM
        else:
            if S < K:
                return -1.0
            elif S > K:
                return 0.0
            else:
                return -0.5  # S == K, ATM
    d1_val = _d1(S, K, T, r, sigma)
    if option_type == "CALL":
        return norm.cdf(d1_val)
    else:
        return norm.cdf(d1_val) - 1


def calc_gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Calculate Gamma."""
    if T <= 0 or sigma <= 0:
        return 0.0
    d1_val = _d1(S, K, T, r, sigma)
    return norm.pdf(d1_val) / (S * sigma * math.sqrt(T))


def calc_theta(S: float, K: float, T: float, r: float, sigma: float, option_type: Literal["CALL", "PUT"]) -> float:
    """Calculate Theta (daily, in dollars)."""
    if T <= 0 or sigma <= 0:
        return 0.0
    d1_val = _d1(S, K, T, r, sigma)
    d2_val = _d2(S, K, T, r, sigma)
    term1 = -(S * norm.pdf(d1_val) * sigma) / (2 * math.sqrt(T))
    if option_type == "CALL":
        return (term1 - r * K * math.exp(-r * T) * norm.cdf(d2_val)) / 365
    else:
        return (term1 + r * K * math.exp(-r * T) * norm.cdf(-d2_val)) / 365


def calc_vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Calculate Vega (per 1% change in IV)."""
    if T <= 0 or sigma <= 0:
        return 0.0
    d1_val = _d1(S, K, T, r, sigma)
    return S * norm.pdf(d1_val) * math.sqrt(T) / 100


def calc_rho(S: float, K: float, T: float, r: float, sigma: float, option_type: Literal["CALL", "PUT"]) -> float:
    """Calculate Rho (per 1% change in interest rate)."""
    if T <= 0:
        return 0.0
    d2_val = _d2(S, K, T, r, sigma)
    if option_type == "CALL":
        return K * T * math.exp(-r * T) * norm.cdf(d2_val) / 100
    else:
        return -K * T * math.exp(-r * T) * norm.cdf(-d2_val) / 100


# --- Implied Volatility (Newton-Raphson) ---

def calc_iv(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: Literal["CALL", "PUT"],
    init_sigma: float = 0.3,
) -> float:
    """Calculate implied volatility using Newton-Raphson."""
    sigma = init_sigma
    for _ in range(100):
        price = _bsm_price(S, K, T, r, sigma, option_type)
        vega = S * norm.pdf(_d1(S, K, T, r, sigma)) * math.sqrt(T)
        if vega == 0:
            break
        diff = market_price - price
        sigma += diff / vega
        if abs(diff) < 1e-6:
            break
        if sigma <= 0 or sigma > 5:
            sigma = init_sigma
            break
    return max(0.01, sigma)


def _bsm_price(S: float, K: float, T: float, r: float, sigma: float, option_type: Literal["CALL", "PUT"]) -> float:
    """Black-Scholes-Merton option price."""
    if T <= 0:
        if option_type == "CALL":
            return max(0, S - K)
        else:
            return max(0, K - S)
    d1_val = _d1(S, K, T, r, sigma)
    d2_val = _d2(S, K, T, r, sigma)
    if option_type == "CALL":
        return S * norm.cdf(d1_val) - K * math.exp(-r * T) * norm.cdf(d2_val)
    else:
        return K * math.exp(-r * T) * norm.cdf(-d2_val) - S * norm.cdf(-d1_val)


# --- Data Models ---

@dataclass
class GreekLetters:
    """Greek letters for an option."""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    iv: float  # implied volatility
    theoretical_price: float


@dataclass
class OptionQuote:
    """Option quote from Yahoo Finance."""
    symbol: str
    strike: float
    expiry: str
    option_type: str  # CALL or PUT
    last_price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    iv: float  # implied volatility
    greeks: GreekLetters
    in_the_money: bool
    moneyness: float  # S/K for calls, K/S for puts


@dataclass
class OptionsChain:
    """Full options chain for a symbol."""
    symbol: str
    spot_price: float
    risk_free_rate: float
    expiry_date: str
    calls: list[OptionQuote]
    puts: list[OptionQuote]


# --- Yahoo Finance Options Fetcher ---

class OptionsService:
    """Service for fetching options data and calculating Greek letters."""

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance"
    DEFAULT_RISK_FREE_RATE = 0.05  # 5% annual

    def __init__(self, timeout: float = 10.0, risk_free_rate: float = None):
        self.timeout = timeout
        self.risk_free_rate = risk_free_rate or self.DEFAULT_RISK_FREE_RATE
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

    def _t_to_expiry(self, expiry_str: str) -> float:
        """Convert expiry string to time to expiry in years."""
        try:
            exp_date = datetime.strptime(expiry_str, "%Y-%m-%d")
            today = datetime.now()
            T = (exp_date - today).total_seconds() / (365.25 * 24 * 3600)
            return max(T, 0)
        except ValueError:
            return 0

    async def get_options_chain(
        self, symbol: str, expiry: Optional[str] = None, strike_count: int = 10
    ) -> Optional[OptionsChain]:
        """
        Fetch options chain for a symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL", "2330.TW").
            expiry: Specific expiry date (YYYY-MM-DD). If None, uses nearest.
            strike_count: Number of strikes above/below spot to include.

        Returns:
            OptionsChain object or None.
        """
        client = await self._get_client()
        url = f"{self.BASE_URL}/chart/{symbol}"

        try:
            response = await client.get(
                url,
                params={
                    "interval": "1d",
                    "range": "1mo",
                    "symbol": symbol,
                    "includePrePost": "false",
                },
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise SymbolNotFoundError(f"Symbol not found: {symbol}")
            elif e.response.status_code == 429:
                raise RateLimitError("Yahoo Finance rate limit exceeded")
            else:
                raise NetworkError(f"HTTP error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {str(e)}")

        result = data.get("chart", {}).get("result")
        if not result:
            return None

        meta = result[0].get("meta", {})
        spot_price = meta.get("regularMarketPrice", 0.0)
        if spot_price <= 0:
            # Try to get current price another way
            return None

        # Get option chain data
        options_data = result[0].get("options", {})
        expirations = options_data.get("expirationDates", [])
        all_options = options_data.get("options", [])

        if not expirations:
            return None

        # Pick expiry
        if expiry:
            target_ts = int(datetime.strptime(expiry, "%Y-%m-%d").timestamp())
        else:
            target_ts = min(expirations) if expirations else 0

        # Find options for chosen expiry
        chain_opts = []
        for opt_list in all_options:
            if isinstance(opt_list, list):
                for o in opt_list:
                    exp_ts = o.get("expiration", 0)
                    if abs(exp_ts - target_ts) < 86400:
                        chain_opts.append(o)

        if not chain_opts:
            # Use first expiry
            target_ts = min(expirations)
            for opt_list in all_options:
                if isinstance(opt_list, list):
                    for o in opt_list:
                        exp_ts = o.get("expiration", 0)
                        if abs(exp_ts - target_ts) < 86400:
                            chain_opts.append(o)

        expiry_str = datetime.fromtimestamp(target_ts).strftime("%Y-%m-%d") if target_ts else ""
        T = self._t_to_expiry(expiry_str)

        calls, puts = [], []

        for o in chain_opts:
            strike = o.get("strike", 0)
            opt_type = "CALL" if o.get("type", "") == "call" else "PUT"
            last = o.get("lastPrice", 0)
            bid = o.get("bid", 0)
            ask = o.get("ask", 0)
            vol = o.get("volume", 0) or 0
            oi = o.get("openInterest", 0) or 0

            # Calculate IV from bid/ask midpoint if not provided
            midpoint = (bid + ask) / 2 if bid and ask else last
            iv_val = o.get("impliedVolatility", 0) or 0
            if iv_val <= 0 and midpoint > 0:
                try:
                    iv_val = calc_iv(midpoint, spot_price, strike, T, self.risk_free_rate, opt_type)
                except Exception:
                    iv_val = 0.3

            # Calculate Greeks
            try:
                greeks = GreekLetters(
                    delta=calc_delta(spot_price, strike, T, self.risk_free_rate, iv_val, opt_type),
                    gamma=calc_gamma(spot_price, strike, T, self.risk_free_rate, iv_val),
                    theta=calc_theta(spot_price, strike, T, self.risk_free_rate, iv_val, opt_type),
                    vega=calc_vega(spot_price, strike, T, self.risk_free_rate, iv_val),
                    rho=calc_rho(spot_price, strike, T, self.risk_free_rate, iv_val, opt_type),
                    iv=iv_val,
                    theoretical_price=_bsm_price(spot_price, strike, T, self.risk_free_rate, iv_val, opt_type),
                )
            except Exception:
                greeks = GreekLetters(0, 0, 0, 0, 0, iv_val, midpoint)

            itm = (opt_type == "CALL" and spot_price > strike) or (opt_type == "PUT" and spot_price < strike)
            moneyness = spot_price / strike if strike > 0 else 1.0

            quote = OptionQuote(
                symbol=symbol,
                strike=strike,
                expiry=expiry_str,
                option_type=opt_type,
                last_price=last,
                bid=bid,
                ask=ask,
                volume=vol,
                open_interest=oi,
                iv=iv_val,
                greeks=greeks,
                in_the_money=itm,
                moneyness=moneyness,
            )

            if opt_type == "CALL":
                calls.append(quote)
            else:
                puts.append(quote)

        calls.sort(key=lambda x: x.strike)
        puts.sort(key=lambda x: x.strike)

        # Filter to strikes around spot
        if strike_count > 0 and calls and puts:
            atm_idx_c = min(range(len(calls)), key=lambda i: abs(calls[i].strike - spot_price))
            atm_idx_p = min(range(len(puts)), key=lambda i: abs(puts[i].strike - spot_price))
            half = strike_count // 2
            calls = calls[max(0, atm_idx_c - half) : atm_idx_c + half + 1]
            puts = puts[max(0, atm_idx_p - half) : atm_idx_p + half + 1]

        return OptionsChain(
            symbol=symbol,
            spot_price=spot_price,
            risk_free_rate=self.risk_free_rate,
            expiry_date=expiry_str,
            calls=calls,
            puts=puts,
        )

    async def get_greeks(
        self,
        symbol: str,
        strike: float,
        expiry: str,
        option_type: Literal["CALL", "PUT"],
        iv: Optional[float] = None,
    ) -> Optional[GreekLetters]:
        """
        Get Greek letters for a specific option.

        Args:
            symbol: Underlying symbol.
            strike: Strike price.
            expiry: Expiry date (YYYY-MM-DD).
            option_type: CALL or PUT.
            iv: Implied volatility (optional, will fetch if not provided).

        Returns:
            GreekLetters object.
        """
        S = 0.0
        if iv is None or iv <= 0:
            # Fetch spot and IV
            chain = await self.get_options_chain(symbol, expiry=expiry, strike_count=1)
            if not chain:
                return None
            S = chain.spot_price
            # Find the matching strike
            quotes = chain.calls if option_type == "CALL" else chain.puts
            for q in quotes:
                if abs(q.strike - strike) < 0.01:
                    iv = q.iv
                    break
            if iv is None:
                iv = 0.3
        else:
            # Just get spot price
            client = await self._get_client()
            try:
                resp = await client.get(
                    f"{self.BASE_URL}/chart/{symbol}",
                    params={"interval": "1d", "range": "1d", "symbol": symbol},
                )
                data = resp.json()
                result = data.get("chart", {}).get("result", [])
                if result:
                    S = result[0].get("meta", {}).get("regularMarketPrice", 0.0)
            except Exception:
                return None

        T = self._t_to_expiry(expiry)
        if S <= 0:
            return None

        return GreekLetters(
            delta=calc_delta(S, strike, T, self.risk_free_rate, iv, option_type),
            gamma=calc_gamma(S, strike, T, self.risk_free_rate, iv),
            theta=calc_theta(S, strike, T, self.risk_free_rate, iv, option_type),
            vega=calc_vega(S, strike, T, self.risk_free_rate, iv),
            rho=calc_rho(S, strike, T, self.risk_free_rate, iv, option_type),
            iv=iv,
            theoretical_price=_bsm_price(S, strike, T, self.risk_free_rate, iv, option_type),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

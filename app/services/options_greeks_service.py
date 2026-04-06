"""
Options Greeks & Pricing Service
Black-Scholes pricing, Greeks calculation, implied volatility, strategy analysis
"""

import math
from datetime import datetime, timedelta
from typing import Optional
from scipy.stats import norm
from sqlalchemy.orm import Session

from app.models.options import OptionContract, OptionPosition
from app.services.options_service import OptionsService


class OptionsGreeksService:
    """Service for options Greeks calculations and strategy analysis."""

    def __init__(self, db: Session):
        self.db = db

    def black_scholes_price(
        self,
        S: float,  # Current stock price
        K: float,  # Strike price
        T: float,  # Time to expiration (in years)
        r: float,  # Risk-free rate
        sigma: float,  # Volatility
        option_type: str  # 'CALL' or 'PUT'
    ) -> float:
        """Calculate Black-Scholes theoretical price."""
        if T <= 0:
            # At expiration, intrinsic value
            if option_type == 'CALL':
                return max(S - K, 0)
            else:
                return max(K - S, 0)

        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        if option_type == 'CALL':
            price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

        return price

    def calculate_greeks(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str
    ) -> dict:
        """
        Calculate all Greeks for an option.
        Returns delta, gamma, theta, vega, rho.
        """
        if T <= 0:
            return {
                "delta": 1.0 if option_type == 'CALL' and S > K else (-1.0 if option_type == 'PUT' and S < K else 0),
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
                "rho": 0.0
            }

        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        # Delta
        if option_type == 'CALL':
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1

        # Gamma (same for CALL and PUT)
        gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))

        # Theta
        if option_type == 'CALL':
            theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T))
                     - r * K * math.exp(-r * T) * norm.cdf(d2))
        else:
            theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T))
                     + r * K * math.exp(-r * T) * norm.cdf(-d2))

        # Vega (same for CALL and PUT)
        vega = S * norm.pdf(d1) * math.sqrt(T)

        # Rho
        if option_type == 'CALL':
            rho = K * T * math.exp(-r * T) * norm.cdf(d2)
        else:
            rho = -K * T * math.exp(-r * T) * norm.cdf(-d2)

        # Normalize theta and vega per day
        theta = theta / 365
        vega = vega / 100  # per 1% change in volatility

        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta, 4),
            "vega": round(vega, 4),
            "rho": round(rho, 4)
        }

    def calculate_implied_volatility(
        self,
        market_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str,
        tolerance: float = 0.0001,
        max_iterations: int = 100
    ) -> Optional[float]:
        """
        Calculate implied volatility using Newton-Raphson method.
        Returns IV as a decimal (e.g., 0.25 for 25%).
        """
        if T <= 0 or market_price <= 0:
            return None

        sigma = 0.20  # Initial guess

        for _ in range(max_iterations):
            price = self.black_scholes_price(S, K, T, r, sigma, option_type)
            if price <= 0:
                return None

            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            vega = S * norm.pdf(d1) * math.sqrt(T) / 100

            if abs(vega) < 1e-10:
                break

            diff = market_price - price
            if abs(diff) < tolerance:
                return sigma

            sigma = sigma + diff / vega

            # Keep sigma in reasonable range
            sigma = max(0.01, min(sigma, 5.0))

        return sigma if sigma < 5.0 else None

    def calculate_portfolio_greeks(self, user_id: str, current_prices: dict) -> dict:
        """Calculate aggregate Greeks for all user positions."""
        positions = self.db.query(OptionPosition).filter(
            OptionPosition.user_id == user_id
        ).all()

        total_delta = 0.0
        total_gamma = 0.0
        total_theta = 0.0
        total_vega = 0.0

        risk_free_rate = 0.05  # 5% default

        for pos in positions:
            symbol = pos.underlying_symbol
            if symbol not in current_prices:
                continue

            S = current_prices[symbol]
            K = pos.strike_price
            T = max((pos.expiry_date - datetime.now()).days / 365, 0)
            sigma = pos.implied_volatility or 0.30
            r = risk_free_rate
            option_type = 'CALL' if pos.option_type == 'CALL' else 'PUT'

            multiplier = pos.quantity * (100 if option_type == 'CALL' else 100)

            greeks = self.calculate_greeks(S, K, T, r, sigma, option_type)

            total_delta += greeks["delta"] * multiplier
            total_gamma += greeks["gamma"] * multiplier
            total_theta += greeks["theta"] * multiplier
            total_vega += greeks["vega"] * multiplier

        return {
            "delta": round(total_delta, 2),
            "gamma": round(total_gamma, 4),
            "theta": round(total_theta, 2),
            "vega": round(total_vega, 2)
        }

    def analyze_strategy(
        self,
        strategy_type: str,
        positions: list,
        current_price: float
    ) -> dict:
        """
        Analyze options strategy (Covered Call, Bull Spread, etc.).
        Returns payoff at expiration and max profit/loss.
        """
        payoff_at_expiry = 0
        max_profit = None
        max_loss = None
        breakeven = None

        for pos in positions:
            qty = pos.get("quantity", 1)
            strike = pos.get("strike", current_price)
            premium = pos.get("premium", 0)
            option_type = pos.get("type", "CALL")

            if option_type == "CALL":
                # Long call: profit if price > strike
                intrinsic = max(current_price - strike, 0)
                payoff = intrinsic - premium
            else:
                # Long put: profit if price < strike
                intrinsic = max(strike - current_price, 0)
                payoff = intrinsic - premium

            payoff_at_expiry += payoff * qty * 100

        analysis = {
            "strategy": strategy_type,
            "current_payoff": round(payoff_at_expiry, 2),
            "max_profit": max_profit,
            "max_loss": max_loss,
            "breakeven": breakeven,
            "positions": positions
        }

        return analysis

    def get_strategy_payoff_data(
        self,
        strategy_type: str,
        underlying_price: float,
        strikes: list,
        premiums: list,
        option_types: list,
        quantities: list
    ) -> dict:
        """
        Generate payoff diagram data points for a strategy.
        Returns price vs P/L data for charting.
        """
        price_range = []
        min_price = underlying_price * 0.5
        max_price = underlying_price * 1.5
        step = (max_price - min_price) / 100

        current_price = min_price
        while current_price <= max_price:
            payoff = 0
            for i, strike in enumerate(strikes):
                premium = premiums[i]
                opt_type = option_types[i]
                qty = quantities[i]

                if opt_type == "CALL":
                    intrinsic = max(current_price - strike, 0)
                else:
                    intrinsic = max(strike - current_price, 0)

                position_pnl = (intrinsic - premium) * qty * 100
                payoff += position_pnl

            price_range.append({
                "price": round(current_price, 2),
                "payoff": round(payoff, 2)
            })
            current_price += step

        return {
            "strategy": strategy_type,
            "underlying_price": underlying_price,
            "data": price_range
        }

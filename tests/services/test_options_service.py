"""
Tests for Options Service — Greek Letters calculation.
"""

import pytest
import math
from app.services.options_service import (
    calc_delta,
    calc_gamma,
    calc_theta,
    calc_vega,
    calc_rho,
    calc_iv,
    _bsm_price,
)


class TestGreekLetters:
    """Test Black-Scholes Greek letters."""

    # Spot=100, Strike=100, T=30/365, r=5%, sigma=20%, CALL
    S = 100.0
    K = 100.0
    T = 30 / 365.0
    r = 0.05
    sigma = 0.20

    def test_call_delta_atm(self):
        """ATM call should have delta ~0.5."""
        d = calc_delta(self.S, self.K, self.T, self.r, self.sigma, "CALL")
        assert 0.4 < d < 0.6

    def test_put_delta_atm(self):
        """ATM put should have delta ~-0.5."""
        d = calc_delta(self.S, self.K, self.T, self.r, self.sigma, "PUT")
        assert -0.6 < d < -0.4

    def test_call_delta_itm(self):
        """ITM call should have delta > 0.5."""
        d = calc_delta(110, self.K, self.T, self.r, self.sigma, "CALL")
        assert d > 0.5

    def test_call_delta_otm(self):
        """OTM call should have delta < 0.5."""
        d = calc_delta(90, self.K, self.T, self.r, self.sigma, "CALL")
        assert d < 0.5

    def test_gamma_positive(self):
        """Gamma should always be positive."""
        g = calc_gamma(self.S, self.K, self.T, self.r, self.sigma)
        assert g > 0

    def test_vega_positive(self):
        """Vega should always be positive."""
        v = calc_vega(self.S, self.K, self.T, self.r, self.sigma)
        assert v > 0

    def test_theta_negative_for_short_expiry(self):
        """Theta should be negative (time decay) for short-dated options."""
        t = calc_theta(self.S, self.K, 7 / 365, self.r, self.sigma, "CALL")
        assert t < 0

    def test_rho_call_positive(self):
        """Rho for call should be positive (higher rates = higher call value)."""
        rho = calc_rho(self.S, self.K, self.T, self.r, self.sigma, "CALL")
        assert rho > 0

    def test_rho_put_negative(self):
        """Rho for put should be negative (higher rates = lower put value)."""
        rho = calc_rho(self.S, self.K, self.T, self.r, self.sigma, "PUT")
        assert rho < 0

    def test_iv_calculation(self):
        """IV calculated from market price should be reasonable."""
        # ATM call with 30 days, sigma=20%, price ~3.0
        market_price = 3.0
        iv = calc_iv(market_price, self.S, self.K, self.T, self.r, "CALL")
        assert 0.1 < iv < 0.4

    def test_bsm_price_call(self):
        """BSM price should be positive for ATM call."""
        price = _bsm_price(self.S, self.K, self.T, self.r, self.sigma, "CALL")
        assert price > 0

    def test_zero_time_to_expiry(self):
        """At T=0, greeks should handle gracefully."""
        d = calc_delta(self.S, self.K, 0, self.r, self.sigma, "CALL")
        assert d == 1.0  # CALL at S=K, T=0: in-the-money by definition

    def test_zero_volatility(self):
        """At sigma=0, should not divide by zero."""
        g = calc_gamma(self.S, self.K, self.T, self.r, 0)
        assert g == 0.0

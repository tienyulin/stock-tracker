"""
Tests for Dividend Growth Tracker API
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, patch


class TestDividendPaymentSchema:
    """Test DividendPaymentCreate and DividendPaymentResponse schemas."""

    def test_dividend_payment_create_basic(self):
        from app.schemas.schemas import DividendPaymentCreate

        payment = DividendPaymentCreate(
            symbol="AAPL",
            ex_dividend_date=datetime(2026, 3, 15),
            payment_date=datetime(2026, 4, 15),
            amount_per_share=0.25,
            shares_owned=100,
            currency="USD",
        )
        assert payment.symbol == "AAPL"
        assert payment.amount_per_share == 0.25
        assert payment.shares_owned == 100
        assert payment.currency == "USD"

    def test_dividend_payment_create_auto_total(self):
        from app.schemas.schemas import DividendPaymentCreate

        payment = DividendPaymentCreate(
            symbol="AAPL",
            ex_dividend_date=datetime(2026, 3, 15),
            payment_date=datetime(2026, 4, 15),
            amount_per_share=0.25,
            shares_owned=100,
        )
        assert payment.total_amount is None  # Auto-calculated on backend

    def test_dividend_payment_create_minimal(self):
        from app.schemas.schemas import DividendPaymentCreate

        payment = DividendPaymentCreate(
            symbol="MSFT",
            ex_dividend_date=datetime(2026, 5, 1),
            payment_date=datetime(2026, 6, 1),
            amount_per_share=0.75,
        )
        assert payment.symbol == "MSFT"
        assert payment.shares_owned == 0
        assert payment.currency == "USD"


class TestDividendHoldingSchema:
    """Test DividendHoldingUpdate and DividendHoldingResponse schemas."""

    def test_dividend_holding_update_partial(self):
        from app.schemas.schemas import DividendHoldingUpdate

        update = DividendHoldingUpdate(shares_owned=50.0)
        assert update.shares_owned == 50.0
        assert update.cost_basis is None
        assert update.annual_dividend is None

    def test_dividend_holding_update_full(self):
        from app.schemas.schemas import DividendHoldingUpdate

        update = DividendHoldingUpdate(
            shares_owned=100.0,
            cost_basis=15000.0,
            annual_dividend=3.0,
        )
        assert update.shares_owned == 100.0
        assert update.cost_basis == 15000.0
        assert update.annual_dividend == 3.0


class TestDividendCalendarSchema:
    """Test DividendCalendarEntry schema."""

    def test_dividend_calendar_entry(self):
        from app.schemas.schemas import DividendCalendarEntry

        entry = DividendCalendarEntry(
            symbol="JPM",
            ex_dividend_date=datetime(2026, 7, 1),
            payment_date=datetime(2026, 8, 1),
            amount_per_share=1.15,
        )
        assert entry.symbol == "JPM"
        assert entry.amount_per_share == 1.15


class TestDividendDashboardSchema:
    """Test DividendDashboardResponse schema."""

    def test_dividend_dashboard_response(self):
        from app.schemas.schemas import DividendDashboardResponse

        dashboard = DividendDashboardResponse(
            total_dividends_received=5000.0,
            dividends_this_year=1200.0,
            dividends_last_year=1000.0,
            year_over_year_growth=20.0,
            portfolio_dividend_yield=3.5,
            yield_on_cost=5.2,
            recent_payments=[],
            upcoming_ex_dividends=[],
        )
        assert dashboard.total_dividends_received == 5000.0
        assert dashboard.year_over_year_growth == 20.0
        assert dashboard.portfolio_dividend_yield == 3.5


class TestDividendYieldCalculations:
    """Test dividend yield calculation utilities."""

    def test_calculate_yield(self):
        from app.api.v1.dividends import calculate_yield

        # Normal case
        result = calculate_yield(current_price=100.0, annual_dividend=3.0)
        assert result == 3.0

        # High dividend
        result = calculate_yield(current_price=50.0, annual_dividend=5.0)
        assert result == 10.0

        # Zero price
        result = calculate_yield(current_price=0.0, annual_dividend=3.0)
        assert result == 0.0

        # Negative price
        result = calculate_yield(current_price=-10.0, annual_dividend=3.0)
        assert result == 0.0

    def test_calculate_yield_on_cost(self):
        from app.api.v1.dividends import calculate_yield_on_cost

        # Normal case: $10000 cost, 100 shares, $3/share annual = 3%
        result = calculate_yield_on_cost(cost_basis=10000.0, shares=100.0, annual_dividend=3.0)
        assert result == 3.0

        # Zero cost
        result = calculate_yield_on_cost(cost_basis=0.0, shares=100.0, annual_dividend=3.0)
        assert result == 0.0

        # Zero shares
        result = calculate_yield_on_cost(cost_basis=10000.0, shares=0.0, annual_dividend=3.0)
        assert result == 0.0


class TestDividendModels:
    """Test dividend SQLAlchemy models."""

    def test_dividend_payment_model_fields(self):
        from app.models.dividend import DividendPayment

        # Verify table name
        assert DividendPayment.__tablename__ == "dividend_payments"

    def test_dividend_holding_model_fields(self):
        from app.models.dividend import DividendHolding

        assert DividendHolding.__tablename__ == "dividend_holdings"

    def test_ex_dividend_calendar_model_fields(self):
        from app.models.dividend import ExDividendCalendar

        assert ExDividendCalendar.__tablename__ == "ex_dividend_calendar"

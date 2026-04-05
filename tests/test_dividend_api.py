"""
Tests for Dividend Growth Tracker API endpoints
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, patch


class TestDividendAPIEndpoints:
    """Test dividend API route structure."""

    def test_dividends_router_prefix(self):
        from app.api.v1.dividends import router

        assert router.prefix == "/dividends"
        assert "dividends" in router.tags

    def test_payments_endpoints_exist(self):
        from app.api.v1.dividends import router

        routes = [r.path for r in router.routes]
        assert "/payments" in routes
        assert "/holdings" in routes
        assert "/dashboard" in routes
        assert "/growth/{symbol}" in routes
        assert "/calendar" in routes

    def test_get_payments_method(self):
        from app.api.v1.dividends import router

        routes = {r.path: r.methods for r in router.routes}
        assert "GET" in routes.get("/payments", set())
        assert "POST" in routes.get("/payments", set())

    def test_holdings_crud_methods(self):
        from app.api.v1.dividends import router

        routes = {r.path: r.methods for r in router.routes}
        assert "GET" in routes.get("/holdings", set())
        assert "PUT" in routes.get("/holdings/{symbol}", set())
        assert "DELETE" in routes.get("/holdings/{symbol}", set())


class TestDividendCalendarCRUD:
    """Test ex-dividend calendar CRUD operations."""

    def test_calendar_endpoints(self):
        from app.api.v1.dividends import router

        routes = {r.path: r.methods for r in router.routes}
        assert "GET" in routes.get("/calendar", set())
        assert "POST" in routes.get("/calendar", set())
        assert "DELETE" in routes.get("/calendar/{entry_id}", set())


class TestDividendModelsExport:
    """Test that dividend models are properly exported."""

    def test_models_init_exports_dividend(self):
        from app.models import DividendPayment, DividendHolding, ExDividendCalendar

        assert DividendPayment.__tablename__ == "dividend_payments"
        assert DividendHolding.__tablename__ == "dividend_holdings"
        assert ExDividendCalendar.__tablename__ == "ex_dividend_calendar"

    def test_dividend_holding_fields(self):
        from app.models.dividend import DividendHolding

        # Verify key columns exist by checking __table__.columns
        col_names = [c.name for c in DividendHolding.__table__.columns]
        assert "symbol" in col_names
        assert "shares_owned" in col_names
        assert "cost_basis" in col_names
        assert "annual_dividend" in col_names
        assert "dividend_yield" in col_names
        assert "yield_on_cost" in col_names
        assert "dividend_growth_rate" in col_names

    def test_dividend_payment_fields(self):
        from app.models.dividend import DividendPayment

        col_names = [c.name for c in DividendPayment.__table__.columns]
        assert "symbol" in col_names
        assert "ex_dividend_date" in col_names
        assert "payment_date" in col_names
        assert "amount_per_share" in col_names
        assert "shares_owned" in col_names
        assert "total_amount" in col_names
        assert "currency" in col_names

    def test_ex_dividend_calendar_fields(self):
        from app.models.dividend import ExDividendCalendar

        col_names = [c.name for c in ExDividendCalendar.__table__.columns]
        assert "symbol" in col_names
        assert "ex_dividend_date" in col_names
        assert "payment_date" in col_names
        assert "amount_per_share" in col_names
        assert "is_upcoming" in col_names

"""
Tests for Dividend Growth Tracker API endpoints
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import re


class TestDividendAPIEndpoints:
    """Test dividend API route structure."""

    def test_dividends_router_prefix(self):
        from app.api.v1.dividends import router

        assert router.prefix == "/dividends"
        assert "dividends" in router.tags

    def test_payments_endpoints_exist(self):
        """Verify payment endpoints are defined in the source."""
        with open("app/api/v1/dividends.py") as f:
            content = f.read()

        # Use broader pattern to catch endpoints regardless of formatting
        assert re.search(r'@router\.get\s*\(\s*["\']\/payments["\']', content)
        assert re.search(r'@router\.post\s*\(\s*["\']\/payments["\']', content)
        assert re.search(r'@router\.delete\s*\(\s*["\']\/payments\/\{payment_id\}["\']', content)

    def test_holdings_endpoints_exist(self):
        """Verify holdings endpoints are defined in the source."""
        with open("app/api/v1/dividends.py") as f:
            content = f.read()

        assert re.search(r'@router\.get\s*\(\s*["\']\/holdings["\']', content)
        assert re.search(r'@router\.put\s*\(\s*["\']\/holdings\/\{symbol\}["\']', content)
        assert re.search(r'@router\.delete\s*\(\s*["\']\/holdings\/\{symbol\}["\']', content)

    def test_dashboard_endpoint_exists(self):
        with open("app/api/v1/dividends.py") as f:
            content = f.read()

        assert re.search(r'@router\.get\s*\(\s*["\']\/dashboard["\']', content)

    def test_growth_endpoint_exists(self):
        with open("app/api/v1/dividends.py") as f:
            content = f.read()

        assert re.search(r'@router\.get\s*\(\s*["\']\/growth\/\{symbol\}["\']', content)

    def test_calendar_endpoints_exist(self):
        """Verify calendar endpoints are defined in the source."""
        with open("app/api/v1/dividends.py") as f:
            content = f.read()

        assert re.search(r'@router\.get\s*\(\s*["\']\/calendar["\']', content)
        assert re.search(r'@router\.post\s*\(\s*["\']\/calendar["\']', content)
        assert re.search(r'@router\.delete\s*\(\s*["\']\/calendar\/\{entry_id\}["\']', content)

    def test_router_included_in_api_v1(self):
        """Verify dividends router is included in API v1."""
        with open("app/api/v1/router.py") as f:
            content = f.read()

        assert "dividends" in content
        assert "router.include_router(dividends.router)" in content


class TestDividendCalendarCRUD:
    """Test ex-dividend calendar CRUD operations."""

    def test_calendar_get_post_delete_decorators(self):
        """Verify all calendar CRUD decorators exist."""
        with open("app/api/v1/dividends.py") as f:
            content = f.read()

        # Extract all router decorators
        decorators = re.findall(r'@router\.(get|post|put|delete)\(["\']([^"\']+)', content)
        decorator_map = {(m, p): True for m, p in decorators}

        assert ("get", "/calendar") in decorator_map
        assert ("post", "/calendar") in decorator_map
        assert ("delete", "/calendar/{entry_id}") in decorator_map


class TestDividendModelsExport:
    """Test that dividend models are properly exported."""

    def test_models_init_exports_dividend(self):
        from app.models import DividendPayment, DividendHolding, ExDividendCalendar

        assert DividendPayment.__tablename__ == "dividend_payments"
        assert DividendHolding.__tablename__ == "dividend_holdings"
        assert ExDividendCalendar.__tablename__ == "ex_dividend_calendar"

    def test_dividend_holding_fields(self):
        from app.models.dividend import DividendHolding

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

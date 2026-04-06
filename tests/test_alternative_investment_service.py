"""
Tests for Alternative Investment Service.
"""

from datetime import datetime

import pytest


class TestAlternativeInvestmentService:
    """Test Alternative Investment Service."""

    def test_service_initialization(self):
        """Test service initializes correctly."""
        from app.services.alternative_investment_service import AlternativeInvestmentService
        from unittest.mock import MagicMock

        db = MagicMock()
        service = AlternativeInvestmentService(db)
        assert service.db is db

    def test_rental_yield_calculation(self):
        """Test rental yield calculation."""
        from app.services.alternative_investment_service import AlternativeInvestmentService
        from unittest.mock import MagicMock

        db = MagicMock()
        service = AlternativeInvestmentService(db)

        # Normal case
        yield_pct = service.calculate_rental_yield(12000, 200000)
        assert yield_pct == 6.0

        # Zero property value
        yield_pct = service.calculate_rental_yield(12000, 0)
        assert yield_pct == 0

        # Negative property value
        yield_pct = service.calculate_rental_yield(12000, -100)
        assert yield_pct == 0

    def test_empty_portfolio_summary(self):
        """Test summary for user with no alternative investments."""
        from app.services.alternative_investment_service import AlternativeInvestmentService
        from unittest.mock import MagicMock

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = AlternativeInvestmentService(db)
        summary = service.get_summary(user_id="test-user-id")

        assert summary["total_value"] == 0
        assert summary["total_cost_basis"] == 0
        assert summary["total_unrealized_gain"] == 0
        assert summary["currency"] == "USD"
        assert summary["liquidity_analysis"]["total_value"] == 0

    def test_portfolio_summary_with_investments(self):
        """Test summary calculation with investments."""
        from app.services.alternative_investment_service import AlternativeInvestmentService
        from unittest.mock import MagicMock
        from app.models.alternative_investments import AlternativeInvestment, LiquidityType

        mock_inv = MagicMock(spec=AlternativeInvestment)
        mock_inv.current_value = 100000
        mock_inv.cost_basis = 80000
        mock_inv.liquidity = LiquidityType.ILLIQUID.value
        mock_inv.investment_type = "private_equity"

        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_inv]

        service = AlternativeInvestmentService(db)
        summary = service.get_summary(user_id="test-user-id")

        assert summary["total_value"] == 100000
        assert summary["total_cost_basis"] == 80000
        assert summary["total_unrealized_gain"] == 20000
        assert summary["liquidity_analysis"]["illiquid_value"] == 100000
        assert summary["liquidity_analysis"]["illiquid_percent"] == 100.0

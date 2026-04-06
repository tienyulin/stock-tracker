"""
Tests for Cash Flow Service.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


class TestCashFlowService:
    """Test CashFlowService."""

    def test_service_initialization(self):
        from app.services.cash_flow_service import CashFlowService

        db = MagicMock()
        service = CashFlowService(db)
        assert service.db is db

    def test_create_entry(self):
        from app.services.cash_flow_service import CashFlowService

        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        service = CashFlowService(db)
        _entry = service.create_entry(
            user_id=uuid.uuid4(),
            entry_type="income",
            category="salary",
            amount=5000.0,
            entry_date=date(2026, 4, 1),
            description="Monthly salary",
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.entry_type == "income"
        assert added.category == "salary"
        assert float(added.amount) == 5000.0

    def test_get_monthly_cashflow_with_entries(self):
        from app.services.cash_flow_service import CashFlowService

        db = MagicMock()

        mock_income = MagicMock()
        mock_income.entry_type = "income"
        mock_income.category = "salary"
        mock_income.amount = Decimal("5000")

        mock_expense = MagicMock()
        mock_expense.entry_type = "expense"
        mock_expense.category = "housing"
        mock_expense.amount = Decimal("1500")

        # Mock scalar_one_or_none to return a list-like
        def mock_execute(q):
            result = MagicMock()
            result.scalars.return_value.all.return_value = [mock_income, mock_expense]
            return result

        db.execute = mock_execute

        service = CashFlowService(db)
        summary = service.get_monthly_cashflow(uuid.uuid4(), "2026-04")

        assert summary["total_income"] == 5000.0
        assert summary["total_expense"] == 1500.0
        assert summary["net_cash_flow"] == 3500.0

    def test_get_monthly_cashflow_empty(self):
        from app.services.cash_flow_service import CashFlowService

        db = MagicMock()

        def mock_execute(q):
            result = MagicMock()
            result.scalars.return_value.all.return_value = []
            return result

        db.execute = mock_execute

        service = CashFlowService(db)
        summary = service.get_monthly_cashflow(uuid.uuid4(), "2026-04")

        assert summary["total_income"] == 0.0
        assert summary["total_expense"] == 0.0
        assert summary["net_cash_flow"] == 0.0


class TestEmergencyFundService:
    """Test EmergencyFundService."""

    def test_service_initialization(self):
        from app.services.cash_flow_service import EmergencyFundService

        db = MagicMock()
        service = EmergencyFundService(db)
        assert service.db is db

    def test_upsert_fund_creates_new(self):
        from app.services.cash_flow_service import EmergencyFundService

        db = MagicMock()
        db.execute = MagicMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        service = EmergencyFundService(db)
        _fund = service.upsert_fund(
            user_id=uuid.uuid4(),
            current_amount=10000.0,
            monthly_expenses_estimate=3000.0,
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_get_status_with_no_fund(self):
        from app.services.cash_flow_service import EmergencyFundService

        db = MagicMock()
        db.execute = MagicMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

        service = EmergencyFundService(db)
        status = service.get_status(uuid.uuid4())

        assert status["current_fund"] == 0.0
        assert status["is_adequate"] is False
        assert status["coverage_months"] == 0.0

    def test_get_status_adequate_fund(self):
        from app.services.cash_flow_service import EmergencyFundService
        from app.models.cash_flow_db import EmergencyFundModel

        mock_fund = MagicMock(spec=EmergencyFundModel)
        mock_fund.current_amount = Decimal("18000")
        mock_fund.monthly_expenses_estimate = Decimal("3000")

        db = MagicMock()
        db.execute = MagicMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_fund)))

        service = EmergencyFundService(db)
        status = service.get_status(uuid.uuid4())

        assert status["current_fund"] == 18000.0
        assert status["recommended_ideal"] == 18000.0
        assert status["coverage_months"] == 6.0
        assert status["is_adequate"] is True
        assert status["progress_percentage"] == 100.0


class TestCashFlowForecastService:
    """Test CashFlowForecastService."""

    def test_service_initialization(self):
        from app.services.cash_flow_service import CashFlowForecastService

        db = MagicMock()
        service = CashFlowForecastService(db)
        assert service.db is db

    def test_forecast_no_data(self):
        from app.services.cash_flow_service import CashFlowForecastService

        db = MagicMock()

        def mock_execute(q):
            result = MagicMock()
            result.scalars.return_value.all.return_value = []
            return result

        db.execute = mock_execute

        service = CashFlowForecastService(db)
        result = service.get_forecast(uuid.uuid4(), months=3)

        assert result["forecast_months"] == 3
        assert result["forecasted_balance"] == 0.0
        assert result["confidence_score"] == 0.3

    def test_forecast_invalid_months(self):
        from app.services.cash_flow_service import CashFlowForecastService

        db = MagicMock()
        service = CashFlowForecastService(db)

        with pytest.raises(ValueError, match="months must be 3, 6, or 12"):
            service.get_forecast(uuid.uuid4(), months=5)


class TestLiquidityPlanningService:
    """Test LiquidityPlanningService."""

    def test_service_initialization(self):
        from app.services.cash_flow_service import LiquidityPlanningService

        db = MagicMock()
        service = LiquidityPlanningService(db)
        assert service.db is db

    def test_get_position_with_expenses(self):
        from app.services.cash_flow_service import LiquidityPlanningService

        db = MagicMock()

        mock_income = MagicMock()
        mock_income.entry_type = "income"
        mock_income.category = "salary"
        mock_income.amount = Decimal("5000")

        mock_expense = MagicMock()
        mock_expense.entry_type = "expense"
        mock_expense.category = "housing"
        mock_expense.amount = Decimal("2000")

        def mock_execute(q):
            result = MagicMock()
            result.scalars.return_value.all.return_value = [mock_income, mock_expense]
            return result

        db.execute = mock_execute

        service = LiquidityPlanningService(db)
        pos = service.get_position(uuid.uuid4(), high_liquidity=5000, medium_liquidity=10000, low_liquidity=20000)

        assert pos["high_liquidity"] == 5000
        assert pos["medium_liquidity"] == 10000
        assert pos["low_liquidity"] == 20000
        assert pos["total_liquid_assets"] == 35000
        assert pos["months_of_expenses_covered"] == 17.5


class TestLargeExpenseService:
    """Test LargeExpenseService."""

    def test_service_initialization(self):
        from app.services.cash_flow_service import LargeExpenseService

        db = MagicMock()
        service = LargeExpenseService(db)
        assert service.db is db

    def test_create_expense(self):
        from app.services.cash_flow_service import LargeExpenseService

        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        service = LargeExpenseService(db)
        _expense = service.create(
            user_id=uuid.uuid4(),
            description="New car",
            estimated_amount=30000.0,
            planned_date=date(2027, 4, 1),
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()
        added = db.add.call_args[0][0]
        assert "New car" in added.description
        assert float(added.estimated_amount) == 30000.0

"""
Tests for Fixed Income Service.
"""

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


class TestYieldCalculations:
    """Test yield and duration calculation functions."""

    def test_ytm_government_bond(self):
        from app.services.fixed_income_service import calculate_ytm

        # Face 1000, price 950, coupon 3%, 5 years
        ytm = calculate_ytm(1000, 950, 0.03, 5.0)
        assert 0.03 < ytm < 0.06  # Should be higher than coupon due to discount

    def test_ytm_premium_bond(self):
        from app.services.fixed_income_service import calculate_ytm

        # Face 1000, price 1050, coupon 4%, 3 years
        ytm = calculate_ytm(1000, 1050, 0.04, 3.0)
        assert 0 < ytm < 0.04  # Should be lower than coupon due to premium

    def test_ytm_zero_maturity(self):
        from app.services.fixed_income_service import calculate_ytm

        ytm = calculate_ytm(1000, 1000, 0.05, 0.0)
        assert ytm == 0.05  # Returns coupon rate when matured

    def test_current_yield(self):
        from app.services.fixed_income_service import calculate_current_yield

        # Annual coupon 30, price 950
        cy = calculate_current_yield(30, 950)
        assert abs(cy - 0.03158) < 0.001

    def test_current_yield_zero_price(self):
        from app.services.fixed_income_service import calculate_current_yield

        cy = calculate_current_yield(30, 0)
        assert cy == 0.0


class TestDurationCalculations:
    def test_macauley_duration(self):
        from app.services.fixed_income_service import calculate_macauley_duration

        # 5-year 5% coupon bond at ytm 4%
        dur = calculate_macauley_duration(1000, 0.05, 0.04, 5.0)
        assert 3 < dur < 5  # Duration should be less than maturity

    def test_modified_duration(self):
        from app.services.fixed_income_service import calculate_modified_duration

        mac_dur = 4.5
        mod_dur = calculate_modified_duration(mac_dur, 0.04)
        assert mod_dur < mac_dur  # Modified is always less

    def test_price_change_100bps(self):
        from app.services.fixed_income_service import calculate_price_change

        # 5% modified duration, 100bps yield increase
        delta = calculate_price_change(5.0, 100)
        assert abs(delta + 0.05) < 0.001  # -5% approx


class TestTermDepositCalculations:
    def test_compound_annually(self):
        from app.services.fixed_income_service import calculate_compound_interest

        # 10000, 5%, 2 years annually
        val = calculate_compound_interest(10000, 0.05, 24, "annually")
        assert abs(val - 11025) < 1  # 10000 * 1.05^2

    def test_compound_quarterly(self):
        from app.services.fixed_income_service import calculate_compound_interest

        # 10000, 6%, 1 year quarterly
        val = calculate_compound_interest(10000, 0.06, 12, "quarterly")
        assert abs(val - 10613.64) < 1

    def test_accrued_simple(self):
        from app.services.fixed_income_service import calculate_accrued_term_deposit

        # 10000 at 5% for 182 days
        accrued = calculate_accrued_term_deposit(
            10000, 0.05, date(2026, 1, 1), date(2026, 7, 1)
        )
        assert 240 < accrued < 260  # ~250 expected for 182 days


class TestFixedIncomeService:
    def test_service_initialization(self):
        from app.services.fixed_income_service import FixedIncomeService

        db = MagicMock()
        svc = FixedIncomeService(db)
        assert svc.db is db

    def test_create_bond(self):
        from app.services.fixed_income_service import FixedIncomeService

        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        svc = FixedIncomeService(db)
        _bond = svc.create_bond(
            user_id=uuid.uuid4(),
            name="Test Corp 5Y",
            bond_type="corporate",
            face_value=1000,
            coupon_rate=0.04,
            purchase_price=980,
            purchase_date=date(2025, 1, 1),
            maturity_date=date(2030, 1, 1),
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.name == "Test Corp 5Y"
        assert added.bond_type == "corporate"
        assert float(added.face_value) == 1000
        assert float(added.coupon_rate) == 0.04

    def test_list_bonds_filters_by_user(self):
        from app.services.fixed_income_service import FixedIncomeService

        db = MagicMock()
        db.query = MagicMock()
        mock_query = db.query.return_value
        mock_query.filter.return_value.all.return_value = []

        svc = FixedIncomeService(db)
        svc.list_bonds(uuid.uuid4())

        db.query.assert_called_once()
        mock_query.filter.return_value.all.assert_called_once()

    def test_delete_bond_not_found(self):
        from app.services.fixed_income_service import FixedIncomeService

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        svc = FixedIncomeService(db)
        result = svc.delete_bond(uuid.uuid4(), uuid.uuid4())
        assert result is False


class TestTermDepositService:
    def test_service_initialization(self):
        from app.services.fixed_income_service import TermDepositService

        db = MagicMock()
        svc = TermDepositService(db)
        assert svc.db is db

    def test_create_term_deposit(self):
        from app.services.fixed_income_service import TermDepositService

        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        svc = TermDepositService(db)
        _td = svc.create_term_deposit(
            user_id=uuid.uuid4(),
            name="HSBC 1-Year TD",
            bank_name="HSBC",
            principal=50000,
            interest_rate=0.018,
            term_months=12,
            start_date=date(2026, 1, 1),
            maturity_date=date(2027, 1, 1),
        )

        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.name == "HSBC 1-Year TD"
        assert float(added.principal) == 50000
        assert float(added.interest_rate) == 0.018
        assert added.maturity_value is not None

    def test_get_maturity_alerts_filters_window(self):
        from app.services.fixed_income_service import TermDepositService

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        svc = TermDepositService(db)
        alerts = svc.get_maturity_alerts(uuid.uuid4(), days_ahead=30)
        assert alerts == []

    def test_term_deposit_summary_empty(self):
        from app.services.fixed_income_service import TermDepositService

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        svc = TermDepositService(db)
        summary = svc.get_term_deposit_summary(uuid.uuid4())
        assert summary["total_deposits"] == 0
        assert summary["total_principal"] == 0.0

"""
Tests for ESG Service.
"""

import uuid
from datetime import date
from unittest.mock import MagicMock

import pytest


class TestEsgService:
    """Tests for EsgService."""

    def test_create_esg_score(self):
        from app.services.esg_service import EsgService

        mock_db = MagicMock()
        service = EsgService(mock_db)

        score = service.create_esg_score(
            user_id=uuid.uuid4(),
            ticker="AAPL",
            company_name="Apple Inc.",
            esg_total_score=72.5,
            environmental_score=68.0,
            social_score=75.0,
            governance_score=74.5,
            rating_date=date.today(),
            carbon_footprint_tons=1200.5,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert score.ticker == "AAPL"
        assert score.esg_total_score == 72.5

    def test_get_esg_score(self):
        from app.services.esg_service import EsgService

        mock_db = MagicMock()
        mock_score = MagicMock()
        mock_score.ticker = "MSFT"
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_score

        service = EsgService(mock_db)
        result = service.get_esg_score(uuid.uuid4(), "MSFT")

        assert result.ticker == "MSFT"

    def test_get_esg_score_not_found(self):
        from app.services.esg_service import EsgService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        service = EsgService(mock_db)
        result = service.get_esg_score(uuid.uuid4(), "UNKNOWN")

        assert result is None

    def test_portfolio_esg_summary_empty(self):
        from app.services.esg_service import EsgService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = EsgService(mock_db)
        result = service.get_portfolio_esg_summary(uuid.uuid4())

        assert result["portfolio_esg_score"] == 0.0
        assert result["holdings_count"] == 0

    def test_portfolio_esg_summary_with_scores(self):
        from app.services.esg_service import EsgService

        mock_db = MagicMock()
        mock_score1 = MagicMock()
        mock_score1.esg_total_score = 80.0
        mock_score1.environmental_score = 75.0
        mock_score1.social_score = 82.0
        mock_score1.governance_score = 83.0
        mock_score1.carbon_footprint_tons = 500.0
        mock_score1.water_usage_m3 = 200.0
        mock_score1.waste_tons = 50.0

        mock_score2 = MagicMock()
        mock_score2.esg_total_score = 60.0
        mock_score2.environmental_score = 55.0
        mock_score2.social_score = 62.0
        mock_score2.governance_score = 63.0
        mock_score2.carbon_footprint_tons = 1000.0
        mock_score2.water_usage_m3 = 300.0
        mock_score2.waste_tons = 80.0

        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_score1, mock_score2],
            [],
        ]

        service = EsgService(mock_db)
        result = service.get_portfolio_esg_summary(uuid.uuid4())

        assert result["holdings_count"] == 2
        assert result["portfolio_esg_score"] == 70.0
        assert result["total_carbon_tons"] == 1500.0

    def test_score_to_rating(self):
        from app.services.esg_service import EsgService

        mock_db = MagicMock()
        service = EsgService(mock_db)

        assert service._score_to_rating(90) == "AAA"
        assert service._score_to_rating(80) == "AA"
        assert service._score_to_rating(70) == "A"
        assert service._score_to_rating(60) == "BBB"
        assert service._score_to_rating(50) == "BB"
        assert service._score_to_rating(40) == "B"
        assert service._score_to_rating(20) == "CCC"


class TestControversyAlertService:
    """Tests for ControversyAlertService."""

    def test_check_controversies_weapons(self):
        from app.services.esg_service import ControversyAlertService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ControversyAlertService(mock_db)
        alerts = service.check_controversies(uuid.uuid4(), "BA")

        assert len(alerts) >= 1
        assert any(a.controversy_type == "weapons" for a in alerts)

    def test_check_controversies_clean(self):
        from app.services.esg_service import ControversyAlertService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ControversyAlertService(mock_db)
        alerts = service.check_controversies(uuid.uuid4(), "AAPL")

        # AAPL not in any exclusion list
        assert len(alerts) == 0

    def test_dismiss_alert(self):
        from app.services.esg_service import ControversyAlertService

        mock_db = MagicMock()
        mock_alert = MagicMock()
        mock_alert.status = "active"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert

        service = ControversyAlertService(mock_db)
        result = service.dismiss_alert(uuid.uuid4(), uuid.uuid4())

        assert result.status == "dismissed"
        mock_db.commit.assert_called()


class TestExclusionListService:
    """Tests for ExclusionListService."""

    def test_create_entry(self):
        from app.services.esg_service import ExclusionListService

        mock_db = MagicMock()
        service = ExclusionListService(mock_db)

        entry = service.create_entry(
            user_id=uuid.uuid4(),
            list_type="negative_screening",
            ticker="BA",
            reason="Defense contractor",
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert entry.list_type == "negative_screening"
        assert entry.ticker == "BA"

    def test_delete_entry(self):
        from app.services.esg_service import ExclusionListService

        mock_db = MagicMock()
        mock_entry = MagicMock()
        mock_entry.is_active = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_entry

        service = ExclusionListService(mock_db)
        result = service.delete_entry(uuid.uuid4(), uuid.uuid4())

        assert result is True
        assert mock_entry.is_active is False


class TestEsgPortfolioService:
    """Tests for EsgPortfolioService."""

    def test_screen_portfolio_empty(self):
        from app.services.esg_service import EsgPortfolioService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        service = EsgPortfolioService(mock_db)
        result = service.screen_portfolio(uuid.uuid4())

        assert result["total_holdings"] == 0
        assert result["compliance_score"] == 100.0

    def test_sustainable_alternatives(self):
        from app.services.esg_service import EsgPortfolioService

        mock_db = MagicMock()
        mock_score = MagicMock()
        mock_score.esg_total_score = 50.0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_score

        service = EsgPortfolioService(mock_db)
        alts = service.get_sustainable_alternatives(uuid.uuid4(), "XOM")

        assert len(alts) == 1
        assert alts[0]["alternative_ticker"] == "NEE"
        assert alts[0]["alternative_esg_score"] > 50.0

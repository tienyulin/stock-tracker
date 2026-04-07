"""
Tests for Retirement Readiness Service
"""

import pytest
from uuid import uuid4

from app.schemas.agent_schemas import (
    PersonalFinancialProfile,
)
from app.services.retirement_readiness_service import RetirementReadinessService


@pytest.fixture
def profile_young():
    """Create a young profile for testing."""
    return PersonalFinancialProfile(
        user_id=str(uuid4()),
        age=25,
        annual_income=800000,
        monthly_expenses=40000,
        total_savings=200000,
        risk_tolerance="aggressive",
        investment_experience="beginner",
        financial_goals=["retirement", "emergency_fund"],
    )


@pytest.fixture
def profile_mid_career():
    """Create a mid-career profile for testing."""
    return PersonalFinancialProfile(
        user_id=str(uuid4()),
        age=40,
        annual_income=1500000,
        monthly_expenses=75000,
        total_savings=1500000,
        risk_tolerance="moderate",
        investment_experience="intermediate",
        financial_goals=["retirement", "investment", "education"],
    )


@pytest.fixture
def profile_near_retirement():
    """Create a near-retirement profile for testing."""
    return PersonalFinancialProfile(
        user_id=str(uuid4()),
        age=58,
        annual_income=2000000,
        monthly_expenses=100000,
        total_savings=8000000,
        risk_tolerance="conservative",
        investment_experience="advanced",
        financial_goals=["retirement"],
    )


@pytest.fixture
def service():
    """Create a RetirementReadinessService instance without db."""
    return RetirementReadinessService(db=None)


class TestRetirementReadinessService:
    """Tests for RetirementReadinessService."""

    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service is not None
        assert hasattr(service, "SCORE_EXCELLENT")
        assert hasattr(service, "SCORE_GOOD")
        assert hasattr(service, "SCORE_MODERATE")
        assert hasattr(service, "SCORE_LOW")
        assert service.SCORE_EXCELLENT == 85
        assert service.SCORE_GOOD == 70
        assert service.SCORE_MODERATE == 50
        assert service.SCORE_LOW == 30

    def test_assess_retirement_readiness_young_on_track(self, service, profile_young):
        """Test assessment for young user who is on track."""
        result = service.assess_retirement_readiness(
            profile=profile_young,
            current_savings=500000,
            annual_expenses=480000,
            retirement_age=65,
        )
        assert result is not None
        assert hasattr(result, "readiness_score")
        assert hasattr(result, "readiness_level")
        assert 0 <= result.readiness_score <= 100

    def test_assess_retirement_readiness_mid_career(
        self, service, profile_mid_career
    ):
        """Test assessment for mid-career user."""
        result = service.assess_retirement_readiness(
            profile=profile_mid_career,
            current_savings=1500000,
            annual_expenses=900000,
            retirement_age=65,
        )
        assert result is not None
        assert 0 <= result.readiness_score <= 100
        assert isinstance(result.readiness_level, str)

    def test_assess_retirement_readiness_near_retirement(
        self, service, profile_near_retirement
    ):
        """Test assessment for near-retirement user."""
        result = service.assess_retirement_readiness(
            profile=profile_near_retirement,
            current_savings=8000000,
            annual_expenses=1200000,
            retirement_age=65,
        )
        assert result is not None
        assert 0 <= result.readiness_score <= 100
        assert result.readiness_score >= service.SCORE_MODERATE

    def test_assess_retirement_readiness_already_at_retirement_age(
        self, service, profile_near_retirement
    ):
        """Test assessment when user is at or past retirement age."""
        result = service.assess_retirement_readiness(
            profile=profile_near_retirement,
            current_savings=10000000,
            annual_expenses=1200000,
            retirement_age=65,
        )
        assert result is not None
        assert 0 <= result.readiness_score <= 100

    def test_assess_retirement_readiness_zero_savings(
        self, service, profile_young
    ):
        """Test assessment when user has zero savings."""
        result = service.assess_retirement_readiness(
            profile=profile_young,
            current_savings=0,
            annual_expenses=480000,
            retirement_age=65,
        )
        assert result is not None
        assert 0 <= result.readiness_score <= 100

    def test_calculate_score_method_exists(self, service):
        """Test that _calculate_score method exists."""
        assert hasattr(service, "_calculate_score")

    def test_determine_level_method_exists(self, service):
        """Test that _determine_level method exists."""
        assert hasattr(service, "_determine_level")

    def test_determine_level_excellent(self, service):
        """Test level determination for excellent score."""
        level = service._determine_level(90)
        assert "excellent" in level.lower() or level == "excellent"

    def test_determine_level_good(self, service):
        """Test level determination for good score."""
        level = service._determine_level(78)
        assert isinstance(level, str)

    def test_determine_level_moderate(self, service):
        """Test level determination for moderate score."""
        level = service._determine_level(60)
        assert isinstance(level, str)

    def test_determine_level_low(self, service):
        """Test level determination for low score."""
        level = service._determine_level(25)
        assert isinstance(level, str)

    def test_score_boundaries(self, service, profile_mid_career):
        """Test score boundaries at threshold values."""
        # Test at exactly retirement age boundary
        profile_at_boundary = profile_mid_career.model_copy()
        profile_at_boundary.age = 65
        result = service.assess_retirement_readiness(
            profile=profile_at_boundary,
            current_savings=5000000,
            annual_expenses=600000,
            retirement_age=65,
        )
        assert 0 <= result.readiness_score <= 100


class TestRetirementGapResult:
    """Tests for RetirementGapResult schema integration."""

    def test_retirement_gap_result_schema_exists(self):
        """Verify RetirementGapResult schema exists."""
        from app.schemas.agent_schemas import RetirementGapResult

        assert hasattr(RetirementGapResult, "model_fields")

    def test_retirement_readiness_result_schema_exists(self):
        """Verify RetirementReadinessResult schema exists."""
        from app.schemas.agent_schemas import RetirementReadinessResult

        assert hasattr(RetirementReadinessResult, "model_fields")


class TestEdgeCases:
    """Tests for edge cases."""

    def test_very_high_income(self, service, profile_mid_career):
        """Test with very high income user."""
        profile_mid_career.annual_income = 50000000
        result = service.assess_retirement_readiness(
            profile=profile_mid_career,
            current_savings=10000000,
            annual_expenses=2000000,
            retirement_age=60,
        )
        assert 0 <= result.readiness_score <= 100

    def test_very_low_income(self, service, profile_young):
        """Test with very low income user."""
        profile_young.annual_income = 300000
        result = service.assess_retirement_readiness(
            profile=profile_young,
            current_savings=50000,
            annual_expenses=200000,
            retirement_age=65,
        )
        assert 0 <= result.readiness_score <= 100

    def test_extreme_risk_tolerance(self, service, profile_mid_career):
        """Test with extreme risk tolerance values."""
        profile_mid_career.risk_tolerance = "very_aggressive"
        result = service.assess_retirement_readiness(
            profile=profile_mid_career,
            current_savings=2000000,
            annual_expenses=900000,
            retirement_age=65,
        )
        assert 0 <= result.readiness_score <= 100

    def test_zero_annual_expenses(self, service, profile_young):
        """Test with zero annual expenses (edge case)."""
        result = service.assess_retirement_readiness(
            profile=profile_young,
            current_savings=1000000,
            annual_expenses=0,
            retirement_age=65,
        )
        assert 0 <= result.readiness_score <= 100

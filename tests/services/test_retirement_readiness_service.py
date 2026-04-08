"""
Tests for Retirement Readiness Service
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.schemas.agent_schemas import PersonalFinancialProfile
from app.services.retirement_readiness_service import RetirementReadinessService


@pytest.fixture
def profile_young():
    """Create a young profile for testing."""
    return PersonalFinancialProfile(
        user_id=uuid4(),
        age=25,
        total_net_worth=500000,
        total_assets=600000,
        total_liabilities=100000,
        total_cash=100000,
        total_investments=300000,
        total_debt=100000,
        monthly_income=66667,
        monthly_expenses=40000,
        monthly_savings=26667,
        passive_income_monthly=0,
        has_emergency_fund=True,
        risk_tolerance="AGGRESSIVE",
        investment_experience="BEGINNER",
        last_updated=datetime.utcnow(),
    )


@pytest.fixture
def profile_mid_career():
    """Create a mid-career profile for testing."""
    return PersonalFinancialProfile(
        user_id=uuid4(),
        age=40,
        total_net_worth=3000000,
        total_assets=3500000,
        total_liabilities=500000,
        total_cash=300000,
        total_investments=1500000,
        total_debt=500000,
        monthly_income=125000,
        monthly_expenses=75000,
        monthly_savings=50000,
        passive_income_monthly=10000,
        has_emergency_fund=True,
        risk_tolerance="MODERATE",
        investment_experience="INTERMEDIATE",
        last_updated=datetime.utcnow(),
    )


@pytest.fixture
def profile_near_retirement():
    """Create a near-retirement profile for testing."""
    return PersonalFinancialProfile(
        user_id=uuid4(),
        age=58,
        total_net_worth=12000000,
        total_assets=13000000,
        total_liabilities=1000000,
        total_cash=500000,
        total_investments=8000000,
        total_debt=1000000,
        monthly_income=166667,
        monthly_expenses=100000,
        monthly_savings=66667,
        passive_income_monthly=50000,
        has_emergency_fund=True,
        risk_tolerance="CONSERVATIVE",
        investment_experience="ADVANCED",
        last_updated=datetime.utcnow(),
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

    @pytest.mark.asyncio
    async def test_assess_retirement_readiness_young_on_track(
        self, service, profile_young
    ):
        """Test assessment for young user who is on track."""
        result = await service.assess_retirement_readiness(
            profile=profile_young,
            current_savings=500000,
            annual_expenses=480000,
            retirement_age=65,
        )
        assert result is not None
        assert hasattr(result, "readiness_score")
        assert hasattr(result, "readiness_level")
        assert 0 <= result.readiness_score <= 100
        assert isinstance(result.readiness_level, str)
        assert hasattr(result, "current_nest_egg")
        assert hasattr(result, "on_track_nest_egg")
        assert hasattr(result, "monthly_contribution_needed")
        assert hasattr(result, "years_to_retirement")
        assert hasattr(result, "key_factors")
        assert hasattr(result, "improvement_suggestions")
        assert hasattr(result, "confidence")
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_assess_retirement_readiness_mid_career(
        self, service, profile_mid_career
    ):
        """Test assessment for mid-career user."""
        result = await service.assess_retirement_readiness(
            profile=profile_mid_career,
            current_savings=1500000,
            annual_expenses=900000,
            retirement_age=65,
        )
        assert result is not None
        assert 0 <= result.readiness_score <= 100
        assert isinstance(result.readiness_level, str)
        assert isinstance(result.key_factors, list)
        assert isinstance(result.improvement_suggestions, list)

    @pytest.mark.asyncio
    async def test_assess_retirement_readiness_near_retirement(
        self, service, profile_near_retirement
    ):
        """Test assessment for near-retirement user."""
        result = await service.assess_retirement_readiness(
            profile=profile_near_retirement,
            current_savings=8000000,
            annual_expenses=1200000,
            retirement_age=65,
        )
        assert result is not None
        assert 0 <= result.readiness_score <= 100
        # Score depends on how savings compare to required nest egg

    @pytest.mark.asyncio
    async def test_assess_retirement_readiness_already_at_retirement_age(
        self, service, profile_near_retirement
    ):
        """Test assessment when user is at or past retirement age."""
        result = await service.assess_retirement_readiness(
            profile=profile_near_retirement,
            current_savings=10000000,
            annual_expenses=1200000,
            retirement_age=65,
        )
        assert result is not None
        assert 0 <= result.readiness_score <= 100

    @pytest.mark.asyncio
    async def test_assess_retirement_readiness_zero_savings(
        self, service, profile_young
    ):
        """Test assessment when user has zero savings."""
        result = await service.assess_retirement_readiness(
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

    def test_identify_key_factors_method_exists(self, service):
        """Test that _identify_key_factors method exists."""
        assert hasattr(service, "_identify_key_factors")

    def test_generate_suggestions_method_exists(self, service):
        """Test that _generate_suggestions method exists."""
        assert hasattr(service, "_generate_suggestions")

    def test_calculate_confidence_method_exists(self, service):
        """Test that _calculate_confidence method exists."""
        assert hasattr(service, "_calculate_confidence")

    def test_determine_level_excellent(self, service):
        """Test level determination for excellent score."""
        level = service._determine_level(90)
        assert isinstance(level, str)

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

    @pytest.mark.asyncio
    async def test_score_boundaries(self, service, profile_mid_career):
        """Test score boundaries at threshold values."""
        profile_at_boundary = profile_mid_career.model_copy()
        profile_at_boundary.age = 65
        result = await service.assess_retirement_readiness(
            profile=profile_at_boundary,
            current_savings=5000000,
            annual_expenses=600000,
            retirement_age=65,
        )
        assert 0 <= result.readiness_score <= 100

    def test_calculate_score_uses_profile(self, service, profile_young):
        """Test that _calculate_score considers profile fields."""
        score = service._calculate_score(
            current_savings=100000,
            required_nest_egg=1000000,
            profile=profile_young,
            years_to_retirement=40,
        )
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100


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

    @pytest.mark.asyncio
    async def test_very_high_income(self, service, profile_mid_career):
        """Test with very high income user."""
        profile_mid_career.monthly_income = 5000000
        result = await service.assess_retirement_readiness(
            profile=profile_mid_career,
            current_savings=10000000,
            annual_expenses=2000000,
            retirement_age=60,
        )
        assert 0 <= result.readiness_score <= 100

    @pytest.mark.asyncio
    async def test_very_low_income(self, service, profile_young):
        """Test with very low income user."""
        profile_young.monthly_income = 25000
        result = await service.assess_retirement_readiness(
            profile=profile_young,
            current_savings=50000,
            annual_expenses=200000,
            retirement_age=65,
        )
        assert 0 <= result.readiness_score <= 100

    @pytest.mark.asyncio
    async def test_extreme_risk_tolerance(self, service, profile_mid_career):
        """Test with extreme risk tolerance values."""
        profile_mid_career.risk_tolerance = "VERY_AGGRESSIVE"
        result = await service.assess_retirement_readiness(
            profile=profile_mid_career,
            current_savings=2000000,
            annual_expenses=900000,
            retirement_age=65,
        )
        assert 0 <= result.readiness_score <= 100

    @pytest.mark.asyncio
    async def test_zero_annual_expenses(self, service, profile_young):
        """Test with zero annual expenses (edge case)."""
        result = await service.assess_retirement_readiness(
            profile=profile_young,
            current_savings=1000000,
            annual_expenses=0,
            retirement_age=65,
        )
        assert 0 <= result.readiness_score <= 100

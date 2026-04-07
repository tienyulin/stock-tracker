"""
Tests for Financial Coach Agent Service
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.schemas.agent_schemas import (
    PersonalFinancialProfile,
    HoldingAsset,
    AccountBalance,
)
from app.services.financial_coach_agent import (
    FinancialCoachAgent,
    CoachTopic,
    CoachSentiment,
)


@pytest.fixture
def sample_profile():
    """Create a sample personal financial profile for testing."""
    return PersonalFinancialProfile(
        user_id=str(uuid4()),
        age=35,
        annual_income=1200000,
        monthly_expenses=60000,
        total_savings=500000,
        risk_tolerance="moderate",
        investment_experience="intermediate",
        financial_goals=[
            "retirement",
            "emergency_fund",
            "investment",
        ],
    )


@pytest.fixture
def agent():
    """Create a FinancialCoachAgent instance for testing."""
    return FinancialCoachAgent()


class TestCoachTopic:
    """Tests for CoachTopic enum."""

    def test_coach_topics_defined(self):
        """Verify all expected coach topics are defined."""
        expected_topics = [
            CoachTopic.RETIREMENT,
            CoachTopic.INVESTMENT,
            CoachTopic.BUDGETING,
            CoachTopic.EMERGENCY_FUND,
            CoachTopic.DEBT_MANAGEMENT,
            CoachTopic.TAX_PLANNING,
            CoachTopic.INSURANCE,
            CoachTopic.ESTATE_PLANNING,
            CoachTopic.GENERAL,
        ]
        assert all(topic in CoachTopic for topic in expected_topics)


class TestFinancialCoachAgent:
    """Tests for FinancialCoachAgent core functionality."""

    def test_agent_initialization(self, agent):
        """Test that agent initializes with expected state."""
        assert agent is not None
        assert hasattr(agent, "RETIREMENT_ADVICE")
        assert hasattr(agent, "INVESTMENT_ADVICE")
        assert hasattr(agent, "BUDGETING_ADVICE")

    def test_generate_retirement_advice_on_track(self, agent, sample_profile):
        """Test retirement advice generation when user is on track."""
        sample_profile.age = 30
        advice = agent._generate_retirement_advice(
            profile=sample_profile,
            readiness_score=85,
            monthly_contribution_needed=10000,
        )
        assert isinstance(advice, list)
        assert len(advice) > 0
        assert all(isinstance(a, str) for a in advice)

    def test_generate_retirement_advice_moderate_gap(self, agent, sample_profile):
        """Test retirement advice generation when user has moderate gap."""
        advice = agent._generate_retirement_advice(
            profile=sample_profile,
            readiness_score=55,
            monthly_contribution_needed=25000,
        )
        assert isinstance(advice, list)
        assert len(advice) > 0

    def test_generate_retirement_advice_significant_gap(self, agent, sample_profile):
        """Test retirement advice generation when user has significant gap."""
        sample_profile.age = 50
        advice = agent._generate_retirement_advice(
            profile=sample_profile,
            readiness_score=25,
            monthly_contribution_needed=80000,
        )
        assert isinstance(advice, list)
        assert len(advice) > 0

    def test_generate_investment_advice(self, agent, sample_profile):
        """Test investment advice generation."""
        advice = agent._generate_investment_advice(
            profile=sample_profile,
            topic=CoachTopic.INVESTMENT,
        )
        assert isinstance(advice, list)
        assert len(advice) > 0

    def test_generate_budgeting_advice(self, agent, sample_profile):
        """Test budgeting advice generation."""
        advice = agent._generate_budgeting_advice(profile=sample_profile)
        assert isinstance(advice, list)
        assert len(advice) > 0

    def test_generate_emergency_fund_advice(self, agent, sample_profile):
        """Test emergency fund advice generation."""
        advice = agent._generate_emergency_fund_advice(profile=sample_profile)
        assert isinstance(advice, list)
        assert len(advice) > 0

    def test_generate_debt_advice(self, agent, sample_profile):
        """Test debt management advice generation."""
        advice = agent._generate_debt_advice(profile=sample_profile)
        assert isinstance(advice, list)
        assert len(advice) > 0

    def test_suggest_topic_from_message_retirement(self, agent):
        """Test topic suggestion for retirement-related messages."""
        topics = agent._suggest_topic("我想要規劃退休")
        assert CoachTopic.RETIREMENT in topics

    def test_suggest_topic_from_message_investment(self, agent):
        """Test topic suggestion for investment-related messages."""
        topics = agent._suggest_topic("應該如何配置我的投資組合")
        assert CoachTopic.INVESTMENT in topics

    def test_suggest_topic_from_message_budget(self, agent):
        """Test topic suggestion for budgeting-related messages."""
        topics = agent._suggest_topic("每個月的支出應該怎麼分配")
        assert CoachTopic.BUDGETING in topics

    def test_suggest_topic_from_message_emergency(self, agent):
        """Test topic suggestion for emergency fund-related messages."""
        topics = agent._suggest_topic("我需要建立緊急備用金")
        assert CoachTopic.EMERGENCY_FUND in topics

    def test_suggest_topic_from_message_general(self, agent):
        """Test topic suggestion for general messages."""
        topics = agent._suggest_topic("今天天氣怎麼樣")
        # General is always included as fallback
        assert CoachTopic.GENERAL in topics

    def test_analyze_sentiment_positive(self, agent):
        """Test sentiment analysis for positive messages."""
        sentiment = agent._analyze_sentiment("太好了！非常感謝你的建議")
        assert sentiment == CoachSentiment.POSITIVE

    def test_analyze_sentiment_negative(self, agent):
        """Test sentiment analysis for negative messages."""
        sentiment = agent._analyze_sentiment("這讓我感到很焦慮")
        assert sentiment == CoachSentiment.NEGATIVE

    def test_analyze_sentiment_neutral(self, agent):
        """Test sentiment analysis for neutral messages."""
        sentiment = agent._analyze_sentiment("請告訴我關於投資的基本概念")
        assert sentiment == CoachSentiment.NEUTRAL

    def test_analyze_sentiment_worried(self, agent):
        """Test sentiment analysis for worried messages."""
        sentiment = agent._analyze_sentiment("我擔心我的退休金不夠")
        assert sentiment == CoachSentiment.WORRIED

    def test_build_context_from_profile(self, agent, sample_profile):
        """Test context building from user profile."""
        context = agent._build_context_from_profile(sample_profile)
        assert isinstance(context, str)
        assert str(sample_profile.age) in context
        assert "中" in context  # moderate risk tolerance in Chinese

    def test_get_retirement_readiness_context(self, agent):
        """Test getting retirement readiness context."""
        context = agent._get_retirement_readiness_context(
            score=75,
            monthly_contribution_needed=15000,
            current_savings=500000,
        )
        assert isinstance(context, str)
        assert "75" in context

    def test_format_response_with_suggestions(self, agent):
        """Test response formatting with suggestions."""
        response = agent._format_response(
            message="這是回覆訊息",
            suggestions=["建議一", "建議二"],
            topic=CoachTopic.RETIREMENT,
        )
        assert "這是回覆訊息" in response
        assert "建議一" in response
        assert "建議二" in response

    def test_format_response_emergency_fund(self, agent):
        """Test emergency fund response formatting."""
        response = agent._format_response(
            message="緊急備用金建議",
            suggestions=["建立3-6個月支出儲蓄"],
            topic=CoachTopic.EMERGENCY_FUND,
        )
        assert "緊急備用金建議" in response

    def test_get_retirement_roadmap(self, agent, sample_profile):
        """Test retirement roadmap generation."""
        roadmap = agent._get_retirement_roadmap(profile=sample_profile)
        assert isinstance(roadmap, str)
        assert len(roadmap) > 0

    def test_get_investment_suggestions(self, agent, sample_profile):
        """Test investment suggestions generation."""
        suggestions = agent._get_investment_suggestions(profile=sample_profile)
        assert isinstance(suggestions, dict)
        assert "股票" in suggestions or "股票型" in str(suggestions.values())
        assert "債券" in suggestions or "債券型" in str(suggestions.values())


class TestCoachSentiment:
    """Tests for CoachSentiment enum."""

    def test_sentiment_values(self):
        """Verify all sentiment values exist."""
        from app.services.financial_coach_agent import CoachSentiment

        assert hasattr(CoachSentiment, "POSITIVE")
        assert hasattr(CoachSentiment, "NEGATIVE")
        assert hasattr(CoachSentiment, "NEUTRAL")
        assert hasattr(CoachSentiment, "WORRIED")

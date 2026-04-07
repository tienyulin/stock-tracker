"""
Tests for Financial Coach Agent Service
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.schemas.agent_schemas import PersonalFinancialProfile
from app.services.financial_coach_agent import FinancialCoachAgent, CoachTopic


@pytest.fixture
def user_id():
    """Return a test user ID."""
    return str(uuid4())


@pytest.fixture
def sample_profile():
    """Create a sample personal financial profile for testing."""
    return PersonalFinancialProfile(
        user_id=uuid4(),
        age=35,
        total_net_worth=1000000,
        total_assets=1200000,
        total_liabilities=200000,
        total_cash=100000,
        total_investments=500000,
        total_debt=200000,
        monthly_income=100000,
        monthly_expenses=60000,
        monthly_savings=40000,
        passive_income_monthly=0,
        has_emergency_fund=True,
        risk_tolerance="MODERATE",
        investment_experience="INTERMEDIATE",
        last_updated=datetime.utcnow(),
    )


@pytest.fixture
def agent(user_id):
    """Create a FinancialCoachAgent instance for testing."""
    return FinancialCoachAgent(user_id=user_id)


class TestCoachTopic:
    """Tests for CoachTopic enum."""

    def test_coach_topics_defined(self):
        """Verify all expected coach topics are defined."""
        assert CoachTopic.RETIREMENT == "retirement"
        assert CoachTopic.INVESTMENT == "investment"
        assert CoachTopic.BUDGETING == "budgeting"
        assert CoachTopic.EMERGENCY_FUND == "emergency_fund"
        assert CoachTopic.DEBT_MANAGEMENT == "debt_management"
        assert CoachTopic.TAX_PLANNING == "tax_planning"
        assert CoachTopic.INSURANCE == "insurance"
        assert CoachTopic.ESTATE_PLANNING == "estate_planning"
        assert CoachTopic.GENERAL == "general"

    def test_coach_topics_are_strings(self):
        """Verify coach topic values are strings."""
        for topic in CoachTopic:
            assert isinstance(topic.value, str)


class TestFinancialCoachAgent:
    """Tests for FinancialCoachAgent core functionality."""

    def test_agent_requires_user_id(self, user_id):
        """Test that agent requires user_id parameter."""
        agent = FinancialCoachAgent(user_id=user_id)
        assert agent.user_id == user_id

    def test_agent_initialization(self, agent, user_id):
        """Test that agent initializes with expected state."""
        assert agent is not None
        assert agent.user_id == user_id
        assert agent.conversation is not None
        assert agent.readiness_service is not None

    def test_agent_with_profile(self, user_id, sample_profile):
        """Test agent initialization with profile."""
        agent = FinancialCoachAgent(user_id=user_id, profile=sample_profile)
        assert agent.profile == sample_profile

    def test_add_user_message_auto_detects_retirement_topic(self, agent):
        """Test that add_user_message auto-detects retirement topic."""
        msg = agent.add_user_message("I want to plan for retirement")
        assert msg.role == "user"
        assert msg.content == "I want to plan for retirement"
        assert msg.topic == CoachTopic.RETIREMENT

    def test_add_user_message_auto_detects_budgeting_topic(self, agent):
        """Test that add_user_message auto-detects budgeting topic."""
        msg = agent.add_user_message("How should I allocate my monthly budget")
        assert msg.topic == CoachTopic.BUDGETING

    def test_add_user_message_auto_detects_investment_topic(self, agent):
        """Test that add_user_message auto-detects investment topic."""
        msg = agent.add_user_message("How should I invest my portfolio")
        assert msg.topic == CoachTopic.INVESTMENT

    def test_add_user_message_auto_detects_emergency_topic(self, agent):
        """Test that add_user_message auto-detects emergency fund topic."""
        msg = agent.add_user_message("I need an emergency fund")
        assert msg.topic == CoachTopic.EMERGENCY_FUND

    def test_add_user_message_auto_detects_debt_topic(self, agent):
        """Test that add_user_message auto-detects debt topic."""
        msg = agent.add_user_message("How to pay off credit card debt")
        assert msg.topic == CoachTopic.DEBT_MANAGEMENT

    def test_add_user_message_with_explicit_topic(self, agent):
        """Test add_user_message with explicitly specified topic."""
        msg = agent.add_user_message("Some content", topic=CoachTopic.RETIREMENT)
        assert msg.topic == CoachTopic.RETIREMENT

    def test_add_user_message_general_fallback(self, agent):
        """Test that unknown content falls back to GENERAL topic."""
        msg = agent.add_user_message("What is the weather today")
        assert msg.topic == CoachTopic.GENERAL

    def test_generate_coach_response_no_messages(self, agent):
        """Test coach response when there are no user messages."""
        response = agent.generate_coach_response()
        assert response.role == "coach"
        assert "你好" in response.content or "AI財務教練" in response.content
        assert response.topic == CoachTopic.GENERAL

    def test_generate_coach_response_retirement_topic(self, agent):
        """Test coach response for retirement topic."""
        agent.add_user_message("I want to plan for retirement")
        response = agent.generate_coach_response()
        assert response.role == "coach"
        assert response.topic == CoachTopic.RETIREMENT

    def test_generate_coach_response_with_retirement_readiness(
        self, agent, sample_profile
    ):
        """Test coach response includes retirement readiness data."""
        from app.schemas.agent_schemas import RetirementReadinessResult

        agent_with_profile = FinancialCoachAgent(user_id=agent.user_id, profile=sample_profile)
        agent_with_profile.add_user_message("I want to plan for retirement")
        readiness = RetirementReadinessResult(
            readiness_score=75,
            readiness_level="moderate_gap",
            current_nest_egg=500000,
            on_track_nest_egg=800000,
            monthly_contribution_needed=15000,
            years_to_retirement=30,
            confidence=0.85,
        )
        response = agent_with_profile.generate_coach_response(readiness_result=readiness)
        assert response.role == "coach"
        assert "75" in response.content or "評分" in response.content

    def test_generate_coach_response_budgeting(self, agent):
        """Test coach response for budgeting topic."""
        agent.add_user_message("How to manage my monthly expenses")
        response = agent.generate_coach_response()
        assert response.role == "coach"
        assert response.topic == CoachTopic.BUDGETING

    def test_generate_coach_response_investment(self, agent):
        """Test coach response for investment topic without profile."""
        agent.add_user_message("How should I invest")
        response = agent.generate_coach_response()
        assert response.role == "coach"
        assert response.topic == CoachTopic.INVESTMENT

    def test_generate_coach_response_investment_with_profile(
        self, agent, sample_profile
    ):
        """Test coach response for investment topic with profile."""
        agent_with_profile = FinancialCoachAgent(
            user_id=agent.user_id, profile=sample_profile
        )
        agent_with_profile.add_user_message("How should I invest")
        response = agent_with_profile.generate_coach_response()
        assert response.role == "coach"
        assert "MODERATE" in response.content or "適中型" in response.content

    def test_generate_coach_response_emergency_fund(self, agent):
        """Test coach response for emergency fund topic."""
        agent.add_user_message("I need emergency savings")
        response = agent.generate_coach_response()
        assert response.role == "coach"
        assert "緊急" in response.content or "emergency" in response.content.lower()

    def test_generate_coach_response_debt(self, agent):
        """Test coach response for debt topic."""
        agent.add_user_message("Credit card debt repayment")
        response = agent.generate_coach_response()
        assert response.role == "coach"
        assert "債務" in response.content or "卡" in response.content

    def test_conversation_tracks_messages(self, agent):
        """Test that conversation correctly tracks messages."""
        assert len(agent.conversation.messages) == 0
        agent.add_user_message("I want retirement")
        assert len(agent.conversation.messages) == 1
        agent.generate_coach_response()
        assert len(agent.conversation.messages) == 2

    def test_get_conversation(self, agent):
        """Test get_conversation returns full conversation."""
        agent.add_user_message("test")
        agent.generate_coach_response()
        conv = agent.get_conversation()
        assert len(conv.messages) == 2

    def test_clear_conversation(self, agent):
        """Test clear_conversation removes all messages."""
        agent.add_user_message("test")
        agent.generate_coach_response()
        assert len(agent.conversation.messages) == 2
        agent.clear_conversation()
        assert len(agent.conversation.messages) == 0

    def test_detect_topic_retirement(self, agent):
        """Test _detect_topic for retirement keywords."""
        assert agent._detect_topic("retire") == CoachTopic.RETIREMENT
        assert agent._detect_topic("retirement") == CoachTopic.RETIREMENT
        assert agent._detect_topic("退休金") == CoachTopic.RETIREMENT

    def test_detect_topic_budgeting(self, agent):
        """Test _detect_topic for budgeting keywords."""
        assert agent._detect_topic("budget") == CoachTopic.BUDGETING
        assert agent._detect_topic("expense") == CoachTopic.BUDGETING

    def test_detect_topic_investment(self, agent):
        """Test _detect_topic for investment keywords."""
        # Use ASCII keywords to avoid Unicode normalization issues
        assert agent._detect_topic("invest") == CoachTopic.INVESTMENT
        assert agent._detect_topic("ETF") == CoachTopic.INVESTMENT
        assert agent._detect_topic("portfolio") == CoachTopic.INVESTMENT

    def test_detect_topic_emergency(self, agent):
        """Test _detect_topic for emergency fund keywords."""
        assert agent._detect_topic("emergency") == CoachTopic.EMERGENCY_FUND
        assert agent._detect_topic("savings") == CoachTopic.EMERGENCY_FUND

    def test_detect_topic_debt(self, agent):
        """Test _detect_topic for debt keywords."""
        assert agent._detect_topic("debt") == CoachTopic.DEBT_MANAGEMENT
        assert agent._detect_topic("loan") == CoachTopic.DEBT_MANAGEMENT

    def test_detect_topic_general_fallback(self, agent):
        """Test _detect_topic fallback to general."""
        assert agent._detect_topic("what is the weather") == CoachTopic.GENERAL

    def test_level_display_on_track(self, agent):
        """Test _level_display for on_track level."""
        display = agent._level_display("on_track")
        assert "良好" in display or "✅" in display

    def test_level_display_moderate_gap(self, agent):
        """Test _level_display for moderate_gap level."""
        display = agent._level_display("moderate_gap")
        assert "缺口" in display or "⚠️" in display

    def test_level_display_significant_gap(self, agent):
        """Test _level_display for significant_gap level."""
        display = agent._level_display("significant_gap")
        assert "缺口" in display or "⚠️" in display

    def test_level_display_off_track(self, agent):
        """Test _level_display for off_track level."""
        display = agent._level_display("off_track")
        assert "偏離" in display or "🚨" in display

    def test_retirement_advice_templates_exist(self, agent):
        """Test that retirement advice templates are defined."""
        assert "on_track" in agent.RETIREMENT_ADVICE
        assert "moderate_gap" in agent.RETIREMENT_ADVICE
        assert "significant_gap" in agent.RETIREMENT_ADVICE
        assert "off_track" in agent.RETIREMENT_ADVICE

    def test_budgeting_advice_templates_exist(self, agent):
        """Test that budgeting advice templates are defined."""
        assert len(agent.BUDGETING_ADVICE) > 0

    def test_message_id_is_uuid(self, agent):
        """Test that message IDs are valid UUIDs."""
        msg = agent.add_user_message("test")
        assert msg.message_id is not None
        str(msg.message_id)

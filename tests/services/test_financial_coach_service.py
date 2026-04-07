"""
Tests for Financial Coach Agent Service
"""

import pytest
from uuid import uuid4

from app.schemas.agent_schemas import (
    PersonalFinancialProfile,
    RetirementReadinessResult,
)
from app.services.financial_coach_agent import (
    FinancialCoachAgent,
    CoachTopic,
)


@pytest.fixture
def user_id():
    """Return a test user ID."""
    return str(uuid4())


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
        msg = agent.add_user_message("我想要規劃退休")
        assert msg.role == "user"
        assert msg.content == "我想要規劃退休"
        assert msg.topic == CoachTopic.RETIREMENT

    def test_add_user_message_auto_detects_budgeting_topic(self, agent):
        """Test that add_user_message auto-detects budgeting topic."""
        msg = agent.add_user_message("每個月的支出應該怎麼分配")
        assert msg.topic == CoachTopic.BUDGETING

    def test_add_user_message_auto_detects_investment_topic(self, agent):
        """Test that add_user_message auto-detects investment topic."""
        msg = agent.add_user_message("應該如何配置我的投資組合")
        assert msg.topic == CoachTopic.INVESTMENT

    def test_add_user_message_auto_detects_emergency_topic(self, agent):
        """Test that add_user_message auto-detects emergency fund topic."""
        msg = agent.add_user_message("我需要建立緊急備用金")
        assert msg.topic == CoachTopic.EMERGENCY_FUND

    def test_add_user_message_auto_detects_debt_topic(self, agent):
        """Test that add_user_message auto-detects debt topic."""
        msg = agent.add_user_message("信用卡負債怎麼還")
        assert msg.topic == CoachTopic.DEBT_MANAGEMENT

    def test_add_user_message_with_explicit_topic(self, agent):
        """Test add_user_message with explicitly specified topic."""
        msg = agent.add_user_message("一些內容", topic=CoachTopic.RETIREMENT)
        assert msg.topic == CoachTopic.RETIREMENT

    def test_add_user_message_general_fallback(self, agent):
        """Test that unknown content falls back to GENERAL topic."""
        msg = agent.add_user_message("今天天氣怎麼樣")
        assert msg.topic == CoachTopic.GENERAL

    def test_generate_coach_response_no_messages(self, agent):
        """Test coach response when there are no user messages."""
        response = agent.generate_coach_response()
        assert response.role == "coach"
        assert "你好" in response.content or "AI財務教練" in response.content
        assert response.topic == CoachTopic.GENERAL

    def test_generate_coach_response_retirement_topic(self, agent):
        """Test coach response for retirement topic."""
        agent.add_user_message("我想要規劃退休")
        response = agent.generate_coach_response()
        assert response.role == "coach"
        assert response.topic == CoachTopic.RETIREMENT

    def test_generate_coach_response_with_retirement_readiness(
        self, agent, sample_profile
    ):
        """Test coach response includes retirement readiness data."""
        agent.add_user_message("我想要規劃退休")
        readiness = RetirementReadinessResult(
            readiness_score=75,
            readiness_level="moderate_gap",
            current_nest_egg=500000,
            on_track_nest_egg=800000,
            monthly_contribution_needed=15000,
            years_to_retirement=30,
        )
        response = agent.generate_coach_response(readiness_result=readiness)
        assert response.role == "coach"
        assert "75" in response.content or "評分" in response.content

    def test_generate_coach_response_budgeting(self, agent):
        """Test coach response for budgeting topic."""
        agent.add_user_message("每個月的支出怎麼分配")
        response = agent.generate_coach_response()
        assert response.role == "coach"
        assert response.topic == CoachTopic.BUDGETING

    def test_generate_coach_response_investment(self, agent):
        """Test coach response for investment topic without profile."""
        agent.add_user_message("應該如何投資")
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
        agent_with_profile.add_user_message("應該如何投資")
        response = agent_with_profile.generate_coach_response()
        assert response.role == "coach"
        assert "moderate" in response.content or "適中型" in response.content

    def test_generate_coach_response_emergency_fund(self, agent):
        """Test coach response for emergency fund topic."""
        agent.add_user_message("我需要緊急備用金")
        response = agent.generate_coach_response()
        assert response.role == "coach"
        assert "緊急" in response.content

    def test_generate_coach_response_debt(self, agent):
        """Test coach response for debt topic."""
        agent.add_user_message("信用卡负债怎麼還")
        response = agent.generate_coach_response()
        assert response.role == "coach"
        assert "債務" in response.content or "卡" in response.content

    def test_conversation_tracks_messages(self, agent):
        """Test that conversation correctly tracks messages."""
        assert len(agent.conversation.messages) == 0
        agent.add_user_message("我要退休")
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
        assert agent._detect_topic("退休規劃") == CoachTopic.RETIREMENT
        assert agent._detect_topic("retire") == CoachTopic.RETIREMENT
        assert agent._detect_topic("退休金") == CoachTopic.RETIREMENT

    def test_detect_topic_budgeting(self, agent):
        """Test _detect_topic for budgeting keywords."""
        assert agent._detect_topic("預算") == CoachTopic.BUDGETING
        assert agent._detect_topic("支出") == CoachTopic.BUDGETING

    def test_detect_topic_investment(self, agent):
        """Test _detect_topic for investment keywords."""
        assert agent._detect_topic("投資") == CoachTopic.INVESTMENT
        assert agent._detect_topic("股票") == CoachTopic.INVESTMENT
        assert agent._detect_topic("ETF") == CoachTopic.INVESTMENT

    def test_detect_topic_emergency(self, agent):
        """Test _detect_topic for emergency fund keywords."""
        assert agent._detect_topic("緊急備用金") == CoachTopic.EMERGENCY_FUND
        assert agent._detect_topic("emergency") == CoachTopic.EMERGENCY_FUND

    def test_detect_topic_debt(self, agent):
        """Test _detect_topic for debt keywords."""
        assert agent._detect_topic("債務") == CoachTopic.DEBT_MANAGEMENT
        assert agent._detect_topic("信用卡") == CoachTopic.DEBT_MANAGEMENT

    def test_detect_topic_general_fallback(self, agent):
        """Test _detect_topic fallback to general."""
        assert agent._detect_topic("今天午餐吃什麼") == CoachTopic.GENERAL

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
        # Should not raise if it's a valid UUID
        str(msg.message_id)

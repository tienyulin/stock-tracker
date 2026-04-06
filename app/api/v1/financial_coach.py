"""
Financial Coach API v1 routes.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/coach", tags=["Financial Coach"])


class CoachMessageRequest(BaseModel):
    content: str
    topic: Optional[str] = None


class CoachMessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    topic: Optional[str]
    created_at: str


class CoachConversationResponse(BaseModel):
    user_id: str
    messages: list[CoachMessageResponse]
    current_focus: Optional[str]
    updated_at: str


class RetirementReadinessRequest(BaseModel):
    current_savings: float
    annual_expenses: float
    retirement_age: int = 65


class RetirementReadinessResponse(BaseModel):
    readiness_score: float
    readiness_level: str
    current_nest_egg: float
    on_track_nest_egg: float
    monthly_contribution_needed: float
    years_to_retirement: int
    key_factors: list[str]
    improvement_suggestions: list[str]
    confidence: float
    assessed_at: str


# In-memory conversation store per user (in production, use Redis/DB)
_conversations: dict[str, dict] = {}


@router.post("/message", response_model=CoachMessageResponse)
async def send_coach_message(
    request: CoachMessageRequest,
    current_user = Depends(get_current_user),
):
    """Send a message to the financial coach and get a response."""
    from app.services.financial_coach_agent import FinancialCoachAgent
    from app.services.retirement_readiness_service import RetirementReadinessService

    user_id = str(current_user.id)

    # Get or create conversation
    if user_id not in _conversations:
        _conversations[user_id] = {"agent": None, "readiness": None}

    conv_data = _conversations[user_id]
    agent: FinancialCoachAgent = conv_data.get("agent")

    if agent is None:
        # Create new agent (without profile for now - will be enhanced later)
        agent = FinancialCoachAgent(user_id=user_id)
        conv_data["agent"] = agent

    # Add user message
    agent.add_user_message(request.content, request.topic)

    # Get readiness if available
    readiness_result = conv_data.get("readiness")

    # Generate coach response
    coach_msg = agent.generate_coach_response(readiness_result)

    return CoachMessageResponse(
        message_id=str(coach_msg.message_id),
        role=coach_msg.role,
        content=coach_msg.content,
        topic=coach_msg.topic,
        created_at=coach_msg.created_at.isoformat(),
    )


@router.get("/conversation", response_model=CoachConversationResponse)
async def get_coach_conversation(
    current_user = Depends(get_current_user),
):
    """Get the current conversation with the financial coach."""
    user_id = str(current_user.id)

    if user_id not in _conversations:
        return CoachConversationResponse(
            user_id=user_id,
            messages=[],
            current_focus=None,
            updated_at="",
        )

    agent: FinancialCoachAgent = _conversations[user_id].get("agent")
    if agent is None:
        return CoachConversationResponse(
            user_id=user_id,
            messages=[],
            current_focus=None,
            updated_at="",
        )

    conv = agent.get_conversation()
    return CoachConversationResponse(
        user_id=conv.user_id,
        messages=[
            CoachMessageResponse(
                message_id=str(m.message_id),
                role=m.role,
                content=m.content,
                topic=m.topic,
                created_at=m.created_at.isoformat(),
            )
            for m in conv.messages
        ],
        current_focus=conv.current_focus,
        updated_at=conv.updated_at.isoformat(),
    )


@router.post("/conversation/clear")
async def clear_coach_conversation(
    current_user = Depends(get_current_user),
):
    """Clear the conversation with the financial coach."""
    user_id = str(current_user.id)

    if user_id in _conversations and _conversations[user_id].get("agent"):
        _conversations[user_id]["agent"].clear_conversation()

    return {"status": "cleared"}


@router.post("/retirement-readiness", response_model=RetirementReadinessResponse)
async def assess_retirement_readiness(
    request: RetirementReadinessRequest,
    current_user = Depends(get_current_user),
):
    """Assess retirement readiness and store result for coach context."""
    from app.services.retirement_readiness_service import RetirementReadinessService

    user_id = str(current_user.id)

    # Create a basic profile for assessment
    # In production, this would come from user's stored profile
    from app.schemas.agent_schemas import PersonalFinancialProfile

    # Default profile values for assessment
    profile = PersonalFinancialProfile(
        age=35,  # Default age, would come from user data
        annual_income=request.annual_expenses * 5,  # Rough estimate
        monthly_income=request.annual_expenses / 12,
        monthly_savings=request.annual_expenses / 36,  # Assume 1/3 goes to savings
        total_debt=0,
        risk_tolerance="moderate",
        investment_experience="intermediate",
        investment_knowledge="intermediate",
        has_emergency_fund=True,
    )

    service = RetirementReadinessService()
    result = await service.assess_retirement_readiness(
        profile=profile,
        current_savings=request.current_savings,
        annual_expenses=request.annual_expenses,
        retirement_age=request.retirement_age,
    )

    # Store readiness in conversation context
    if user_id not in _conversations:
        _conversations[user_id] = {"agent": None, "readiness": None}
    _conversations[user_id]["readiness"] = result

    # Update agent context if exists
    if _conversations[user_id].get("agent"):
        _conversations[user_id]["agent"].profile = profile

    return RetirementReadinessResponse(
        readiness_score=result.readiness_score,
        readiness_level=result.readiness_level,
        current_nest_egg=result.current_nest_egg,
        on_track_nest_egg=result.on_track_nest_egg,
        monthly_contribution_needed=result.monthly_contribution_needed,
        years_to_retirement=result.years_to_retirement,
        key_factors=result.key_factors,
        improvement_suggestions=result.improvement_suggestions,
        confidence=result.confidence,
        assessed_at=result.assessed_at.isoformat(),
    )

"""
Wealth Transfer & Dynasty Trust API v1 routes.
"""

from typing import Optional
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/wealth-transfer", tags=["Wealth Transfer"])


# ============== Education Fund Schemas ==============

class EducationFundCreate(BaseModel):
    account_name: str
    account_number_last4: str
    beneficiary_name: str
    beneficiary_relationship: str
    current_balance: float = 0
    target_amount: float
    state: str
    plan_name: str
    projected_college_cost: Optional[float] = None


class EducationFundUpdate(BaseModel):
    current_balance: Optional[float] = None
    total_contributions: Optional[float] = None
    total_withdrawals: Optional[float] = None
    target_amount: Optional[float] = None
    status: Optional[str] = None


class EducationFundResponse(BaseModel):
    id: str
    account_name: str
    beneficiary_name: str
    current_balance: float
    target_amount: float
    progress_percentage: float
    projected_college_cost: Optional[float] = None


# ============== Trust Schemas ==============

class BeneficiaryCreate(BaseModel):
    name: str
    relationship: str
    date_of_birth: Optional[str] = None
    allocation_percentage: float
    conditions: Optional[str] = None
    is_primary: bool = True


class TrustCreate(BaseModel):
    trust_name: str
    trust_type: str
    grantor_name: str
    trustee_name: str
    current_value: float = 0
    beneficiaries: list[BeneficiaryCreate] = []
    creation_date: str
    termination_date: Optional[str] = None
    trust_terms: Optional[str] = None
    annual_distribution_percentage: Optional[float] = None
    generation_skip_enabled: bool = False
    tax_exempt_enabled: bool = False
    notes: Optional[str] = None


class TrustResponse(BaseModel):
    id: str
    trust_name: str
    trust_type: str
    current_value: float
    beneficiary_count: int
    creation_date: str
    generation_skip_enabled: bool


# ============== Timeline Schemas ==============

class TimelineEventCreate(BaseModel):
    event_type: str
    title: str
    description: Optional[str] = None
    event_date: str
    estimated_value: Optional[float] = None
    related_trust_id: Optional[str] = None
    related_education_fund_id: Optional[str] = None


class TimelineEventResponse(BaseModel):
    id: str
    event_type: str
    title: str
    event_date: str
    estimated_value: Optional[float] = None
    status: str


# ============== Family Constitution Schemas ==============

class InvestmentPolicyCreate(BaseModel):
    title: str
    purpose: str
    investment_objectives: str
    asset_allocation_targets: dict = {}
    rebalancing_policy: str
    risk_tolerance: str
    time_horizon: str
    performance_benchmarks: dict = {}


class FamilyConstitutionCreate(BaseModel):
    title: str = "Family Financial Constitution"
    mission_statement: Optional[str] = None
    core_values: list[str] = []
    governance_structure: Optional[str] = None
    succession_plan: Optional[str] = None


class FamilyConstitutionResponse(BaseModel):
    id: str
    title: str
    mission_statement: Optional[str] = None
    core_values: list[str]
    has_investment_policy: bool


# ============== In-memory storage (production would use DB) ==============

_education_funds: dict[str, dict] = {}
_trusts: dict[str, dict] = {}
_timeline_events: dict[str, list] = {}
_constitutions: dict[str, dict] = {}


# ============== Education Fund Endpoints ==============

@router.post("/education-fund", response_model=EducationFundResponse)
async def create_education_fund(
    request: EducationFundCreate,
    current_user = Depends(get_current_user),
):
    """Create a new education fund account."""
    import uuid
    fund_id = str(uuid.uuid4())
    fund = {
        "id": fund_id,
        "user_id": str(current_user.id),
        "account_name": request.account_name,
        "account_number_last4": request.account_number_last4,
        "beneficiary_name": request.beneficiary_name,
        "beneficiary_relationship": request.beneficiary_relationship,
        "current_balance": Decimal(str(request.current_balance)),
        "total_contributions": Decimal("0"),
        "total_withdrawals": Decimal("0"),
        "target_amount": Decimal(str(request.target_amount)),
        "state": request.state,
        "plan_name": request.plan_name,
        "projected_college_cost": Decimal(str(request.projected_college_cost)) if request.projected_college_cost else None,
        "status": "active",
    }
    _education_funds[fund_id] = fund

    target = float(fund["target_amount"])
    current = float(fund["current_balance"])
    progress = min((current / target * 100), 100) if target > 0 else 0

    return EducationFundResponse(
        id=fund_id,
        account_name=request.account_name,
        beneficiary_name=request.beneficiary_name,
        current_balance=current,
        target_amount=target,
        progress_percentage=progress,
        projected_college_cost=float(request.projected_college_cost) if request.projected_college_cost else None,
    )


@router.get("/education-fund", response_model=list[EducationFundResponse])
async def list_education_funds(
    current_user = Depends(get_current_user),
):
    """List all education funds for user."""
    user_id = str(current_user.id)
    results = []
    for fund_id, fund in _education_funds.items():
        if fund.get("user_id") == user_id:
            target = float(fund["target_amount"])
            current = float(fund["current_balance"])
            progress = min((current / target * 100), 100) if target > 0 else 0
            results.append(EducationFundResponse(
                id=fund_id,
                account_name=fund["account_name"],
                beneficiary_name=fund["beneficiary_name"],
                current_balance=current,
                target_amount=target,
                progress_percentage=progress,
                projected_college_cost=float(fund["projected_college_cost"]) if fund.get("projected_college_cost") else None,
            ))
    return results


@router.put("/education-fund/{fund_id}")
async def update_education_fund(
    fund_id: str,
    request: EducationFundUpdate,
    current_user = Depends(get_current_user),
):
    """Update education fund."""
    if fund_id not in _education_funds:
        raise HTTPException(status_code=404, detail="Education fund not found")
    fund = _education_funds[fund_id]
    if fund.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    if request.current_balance is not None:
        fund["current_balance"] = Decimal(str(request.current_balance))
    if request.total_contributions is not None:
        fund["total_contributions"] = Decimal(str(request.total_contributions))
    if request.total_withdrawals is not None:
        fund["total_withdrawals"] = Decimal(str(request.total_withdrawals))
    if request.target_amount is not None:
        fund["target_amount"] = Decimal(str(request.target_amount))
    if request.status is not None:
        fund["status"] = request.status

    return {"status": "updated"}


# ============== Trust Endpoints ==============

@router.post("/trust", response_model=TrustResponse)
async def create_trust(
    request: TrustCreate,
    current_user = Depends(get_current_user),
):
    """Create a new trust account."""
    import uuid
    trust_id = str(uuid.uuid4())
    beneficiaries = []
    for b in request.beneficiaries:
        b_id = str(uuid.uuid4())
        beneficiaries.append({
            "id": b_id,
            "name": b.name,
            "relationship": b.relationship,
            "allocation_percentage": Decimal(str(b.allocation_percentage)),
            "conditions": b.conditions,
            "is_primary": b.is_primary,
        })

    trust = {
        "id": trust_id,
        "user_id": str(current_user.id),
        "trust_name": request.trust_name,
        "trust_type": request.trust_type,
        "grantor_name": request.grantor_name,
        "trustee_name": request.trustee_name,
        "current_value": Decimal(str(request.current_value)),
        "beneficiaries": beneficiaries,
        "creation_date": request.creation_date,
        "termination_date": request.termination_date,
        "trust_terms": request.trust_terms,
        "annual_distribution_percentage": Decimal(str(request.annual_distribution_percentage)) if request.annual_distribution_percentage else None,
        "generation_skip_enabled": request.generation_skip_enabled,
        "tax_exempt_enabled": request.tax_exempt_enabled,
        "notes": request.notes,
    }
    _trusts[trust_id] = trust

    return TrustResponse(
        id=trust_id,
        trust_name=request.trust_name,
        trust_type=request.trust_type,
        current_value=float(request.current_value),
        beneficiary_count=len(beneficiaries),
        creation_date=request.creation_date,
        generation_skip_enabled=request.generation_skip_enabled,
    )


@router.get("/trust", response_model=list[TrustResponse])
async def list_trusts(
    current_user = Depends(get_current_user),
):
    """List all trusts for user."""
    user_id = str(current_user.id)
    results = []
    for trust_id, trust in _trusts.items():
        if trust.get("user_id") == user_id:
            results.append(TrustResponse(
                id=trust_id,
                trust_name=trust["trust_name"],
                trust_type=trust["trust_type"],
                current_value=float(trust["current_value"]),
                beneficiary_count=len(trust.get("beneficiaries", [])),
                creation_date=trust["creation_date"],
                generation_skip_enabled=trust["generation_skip_enabled"],
            ))
    return results


@router.get("/trust/{trust_id}")
async def get_trust(
    trust_id: str,
    current_user = Depends(get_current_user),
):
    """Get trust details."""
    if trust_id not in _trusts:
        raise HTTPException(status_code=404, detail="Trust not found")
    trust = _trusts[trust_id]
    if trust.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    return trust


# ============== Timeline Endpoints ==============

@router.post("/timeline", response_model=TimelineEventResponse)
async def create_timeline_event(
    request: TimelineEventCreate,
    current_user = Depends(get_current_user),
):
    """Create a wealth transfer timeline event."""
    import uuid
    event_id = str(uuid.uuid4())
    user_id = str(current_user.id)

    event = {
        "id": event_id,
        "user_id": user_id,
        "event_type": request.event_type,
        "title": request.title,
        "description": request.description,
        "event_date": request.event_date,
        "estimated_value": Decimal(str(request.estimated_value)) if request.estimated_value else None,
        "related_trust_id": request.related_trust_id,
        "related_education_fund_id": request.related_education_fund_id,
        "status": "planned",
    }

    if user_id not in _timeline_events:
        _timeline_events[user_id] = []
    _timeline_events[user_id].append(event)

    return TimelineEventResponse(
        id=event_id,
        event_type=request.event_type,
        title=request.title,
        event_date=request.event_date,
        estimated_value=float(request.estimated_value) if request.estimated_value else None,
        status="planned",
    )


@router.get("/timeline", response_model=list[TimelineEventResponse])
async def list_timeline_events(
    current_user = Depends(get_current_user),
):
    """List all timeline events for user."""
    user_id = str(current_user.id)
    events = _timeline_events.get(user_id, [])
    return [
        TimelineEventResponse(
            id=e["id"],
            event_type=e["event_type"],
            title=e["title"],
            event_date=e["event_date"],
            estimated_value=float(e["estimated_value"]) if e.get("estimated_value") else None,
            status=e["status"],
        )
        for e in sorted(events, key=lambda x: x["event_date"])
    ]


# ============== Family Constitution Endpoints ==============

@router.post("/family-constitution", response_model=FamilyConstitutionResponse)
async def create_family_constitution(
    request: FamilyConstitutionCreate,
    current_user = Depends(get_current_user),
):
    """Create family constitution."""
    import uuid
    constitution_id = str(uuid.uuid4())
    user_id = str(current_user.id)

    constitution = {
        "id": constitution_id,
        "user_id": user_id,
        "title": request.title,
        "mission_statement": request.mission_statement,
        "core_values": request.core_values,
        "governance_structure": request.governance_structure,
        "succession_plan": request.succession_plan,
        "has_investment_policy": False,
    }
    _constitutions[constitution_id] = constitution

    return FamilyConstitutionResponse(
        id=constitution_id,
        title=request.title,
        mission_statement=request.mission_statement,
        core_values=request.core_values,
        has_investment_policy=False,
    )


@router.get("/family-constitution", response_model=FamilyConstitutionResponse)
async def get_family_constitution(
    current_user = Depends(get_current_user),
):
    """Get user's family constitution."""
    user_id = str(current_user.id)
    for const_id, const in _constitutions.items():
        if const.get("user_id") == user_id:
            return FamilyConstitutionResponse(
                id=const_id,
                title=const["title"],
                mission_statement=const.get("mission_statement"),
                core_values=const.get("core_values", []),
                has_investment_policy=const.get("has_investment_policy", False),
            )
    raise HTTPException(status_code=404, detail="Family constitution not found")


@router.post("/family-constitution/{const_id}/investment-policy", response_model=dict)
async def add_investment_policy(
    const_id: str,
    request: InvestmentPolicyCreate,
    current_user = Depends(get_current_user),
):
    """Add investment policy to family constitution."""
    if const_id not in _constitutions:
        raise HTTPException(status_code=404, detail="Family constitution not found")
    const = _constitutions[const_id]
    if const.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")

    policy = {
        "title": request.title,
        "purpose": request.purpose,
        "investment_objectives": request.investment_objectives,
        "asset_allocation_targets": request.asset_allocation_targets,
        "rebalancing_policy": request.rebalancing_policy,
        "risk_tolerance": request.risk_tolerance,
        "time_horizon": request.time_horizon,
        "performance_benchmarks": request.performance_benchmarks,
    }
    const["investment_policy"] = policy
    const["has_investment_policy"] = True

    return {"status": "added", "policy": policy}

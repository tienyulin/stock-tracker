"""
Estate Planning & Transfer Taxation API
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.estate_service import EstatePlanningService


router = APIRouter(prefix="/estate", tags=["estate"])


# Request Models
class EstateTaxRequest(BaseModel):
    total_value: float
    currency: str = "TWD"
    exchange_rate: float = 31.5


class GiftTaxRequest(BaseModel):
    gift_amount: float
    recipient_relationship: str
    annual_cumulative: float = 0
    currency: str = "TWD"


class RealEstateYieldRequest(BaseModel):
    property_value: float
    monthly_rent: float
    currency: str = "USD"


class InsuranceNeedRequest(BaseModel):
    current_assets: float
    current_debts: float
    annual_income: float
    years_to_protect: int
    currency: str = "USD"


class EstateChecklistRequest(BaseModel):
    total_assets: float
    has_spouse: bool = False


# Endpoints
@router.post("/estate-tax")
def calculate_estate_tax(request: EstateTaxRequest):
    """
    Calculate estimated estate tax liability.
    Based on Taiwan estate tax rules (simplified).
    """
    service = EstatePlanningService()
    result = service.calculate_estate_tax(
        total_estate_value=request.total_value,
        currency=request.currency,
        exchange_rate_to_twd=request.exchange_rate
    )
    return result


@router.post("/gift-tax")
def calculate_gift_tax(request: GiftTaxRequest):
    """
    Calculate gift tax for a given gift.
    Based on Taiwan gift tax rules.
    """
    valid_relationships = [
        "spouse", "child", "parent", "grandparent",
        "grandchild", "sibling", "other"
    ]
    if request.recipient_relationship not in valid_relationships:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid relationship. Must be one of: {', '.join(valid_relationships)}"
        )

    service = EstatePlanningService()
    result = service.calculate_gift_tax(
        gift_amount=request.gift_amount,
        recipient_relationship=request.recipient_relationship,
        annual_cumulative_gifts=request.annual_cumulative,
        currency=request.currency
    )
    return result


@router.post("/real-estate/yield")
def calculate_property_yield(request: RealEstateYieldRequest):
    """
    Calculate rental yield for a real estate property.
    """
    if request.property_value <= 0:
        raise HTTPException(status_code=400, detail="Property value must be positive")
    if request.monthly_rent < 0:
        raise HTTPException(status_code=400, detail="Monthly rent cannot be negative")

    service = EstatePlanningService()
    result = service.calculate_real_estate_yield(
        property_value=request.property_value,
        monthly_rent=request.monthly_rent,
        currency=request.currency
    )
    return result


@router.post("/insurance-needs")
def calculate_insurance_needs(request: InsuranceNeedRequest):
    """
    Calculate recommended life insurance coverage.
    Uses income replacement method.
    """
    if request.years_to_protect <= 0 or request.years_to_protect > 50:
        raise HTTPException(status_code=400, detail="Years to protect must be 1-50")

    service = EstatePlanningService()
    result = service.calculate_life_insurance_needs(
        current_assets=request.current_assets,
        current_debts=request.current_debts,
        annual_income=request.annual_income,
        years_to_protect=request.years_to_protect,
        currency=request.currency
    )
    return result


@router.post("/checklist")
def generate_estate_checklist(request: EstateChecklistRequest):
    """
    Generate estate planning checklist based on assets and family status.
    """
    service = EstatePlanningService()
    result = service.generate_estate_checklist(
        total_assets=request.total_assets,
        has_spouse=request.has_spouse
    )
    return result


@router.get("/summary/{user_id}")
def get_estate_summary(
    user_id: str,
    total_assets: float = Query(...),
    has_spouse: bool = Query(False),
    currency: str = Query("USD")
):
    """
    Get comprehensive estate planning summary.
    """
    service = EstatePlanningService()

    estate_tax = service.calculate_estate_tax(total_assets, currency)
    checklist = service.generate_estate_checklist(total_assets, has_spouse)

    return {
        "user_id": user_id,
        "total_assets": total_assets,
        "currency": currency,
        "estate_tax": estate_tax,
        "planning_checklist": checklist
    }


@router.get("/gift-tracking/{user_id}")
def get_gift_tracking_summary(
    user_id: str,
    annual_gifts: float = Query(0, ge=0),
    currency: str = Query("TWD")
):
    """
    Get gift tax tracking summary for annual reporting.
    """
    remaining_exemption = max(0, EstatePlanningService.ANNUAL_GIFT_EXEMPTION_TWD - annual_gifts)

    return {
        "user_id": user_id,
        "annual_cumulative_gifts": annual_gifts,
        "annual_exemption": EstatePlanningService.ANNUAL_GIFT_EXEMPTION_TWD,
        "remaining_exemption": remaining_exemption,
        "currency": currency,
        "status": "Tax Free" if remaining_exemption > 0 else "Tax Planning Required"
    }

"""
ESG & Sustainable Investing API routes.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.esg import ControversyAlert, EsgScore
from app.schemas.esg_schemas import (
    CarbonFootprintResponse,
    ControversyAlertResponse,
    ControversyCheckResponse,
    EsgScoreCreate,
    EsgScoreResponse,
    EsgTrendResponse,
    ExclusionListCreate,
    ExclusionListResponse,
    ExclusionListUpdate,
    PortfolioCarbonResponse,
    PortfolioEsgSummary,
    PortfolioScreenResponse,
    SustainableAlternativeResponse,
)
from app.services.esg_service import (
    CarbonFootprintService,
    ControversyAlertService,
    EsgPortfolioService,
    EsgService,
    ExclusionListService,
)

router = APIRouter(prefix="/esg", tags=["esg"])


def get_user_id() -> UUID:
    """Placeholder — real auth injected by router-level dependency."""
    return UUID("00000000-0000-0000-0000-000000000000")


UserID = Annotated[UUID, Depends(get_user_id)]


# ─── ESG Scores ───────────────────────────────────────────────────────────────

scores_router = APIRouter(prefix="/scores", tags=["esg-scores"])


@scores_router.post("", response_model=EsgScoreResponse, status_code=status.HTTP_201_CREATED)
def create_esg_score(data: EsgScoreCreate, user_id: UserID, db: Session = Depends(get_db)):
    service = EsgService(db)
    score = service.create_esg_score(
        user_id=user_id,
        ticker=data.ticker,
        company_name=data.company_name,
        esg_total_score=data.esg_total_score,
        environmental_score=data.environmental_score,
        social_score=data.social_score,
        governance_score=data.governance_score,
        rating_date=data.rating_date,
        carbon_footprint_tons=data.carbon_footprint_tons,
        water_usage_m3=data.water_usage_m3,
        waste_tons=data.waste_tons,
        data_source=data.data_source,
    )
    return score


@scores_router.get("/{ticker}", response_model=EsgScoreResponse)
def get_esg_score(ticker: str, user_id: UserID, db: Session = Depends(get_db)):
    service = EsgService(db)
    score = service.get_esg_score(user_id, ticker)
    if not score:
        raise HTTPException(status_code=404, detail=f"ESG score not found for {ticker}")
    return score


@scores_router.get("/portfolio/summary", response_model=PortfolioEsgSummary)
def get_portfolio_esg_summary(user_id: UserID, db: Session = Depends(get_db)):
    service = EsgService(db)
    return service.get_portfolio_esg_summary(user_id)


@scores_router.get("/portfolio/trend/{ticker}", response_model=list[EsgTrendResponse])
def get_esg_trend(ticker: str, months: int = 12, user_id: UserID = None, db: Session = Depends(get_db)):
    service = EsgService(db)
    return service.get_esg_trend(user_id, ticker, months)


# ─── Carbon Footprint ────────────────────────────────────────────────────────

carbon_router = APIRouter(prefix="/portfolio/carbon", tags=["carbon-footprint"])


@carbon_router.get("", response_model=PortfolioCarbonResponse)
def get_portfolio_carbon(user_id: UserID, db: Session = Depends(get_db)):
    service = CarbonFootprintService(db)
    return service.get_portfolio_carbon(user_id)


# ─── Controversy Alerts ─────────────────────────────────────────────────────

alerts_router = APIRouter(prefix="/alerts", tags=["controversy-alerts"])


@alerts_router.get("", response_model=list[ControversyAlertResponse])
def get_active_alerts(user_id: UserID, db: Session = Depends(get_db)):
    service = ControversyAlertService(db)
    return service.get_active_alerts(user_id)


@alerts_router.post("/check/{ticker}", response_model=ControversyCheckResponse)
def check_controversies(ticker: str, user_id: UserID, db: Session = Depends(get_db)):
    service = ControversyAlertService(db)
    alerts = service.check_controversies(user_id, ticker)
    return {
        "ticker": ticker.upper(),
        "has_controversies": len(alerts) > 0,
        "alerts": alerts,
    }


@alerts_router.post("/{alert_id}/dismiss", response_model=ControversyAlertResponse)
def dismiss_alert(alert_id: UUID, user_id: UserID, db: Session = Depends(get_db)):
    service = ControversyAlertService(db)
    alert = service.dismiss_alert(alert_id, user_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


# ─── Exclusion List ──────────────────────────────────────────────────────────

exclusions_router = APIRouter(prefix="/exclusions", tags=["exclusion-list"])


@exclusions_router.get("", response_model=list[ExclusionListResponse])
def get_exclusions(
    user_id: UserID,
    list_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    service = ExclusionListService(db)
    return service.get_exclusions(user_id, list_type)


@exclusions_router.post("", response_model=ExclusionListResponse, status_code=status.HTTP_201_CREATED)
def create_exclusion(data: ExclusionListCreate, user_id: UserID, db: Session = Depends(get_db)):
    service = ExclusionListService(db)
    entry = service.create_entry(
        user_id=user_id,
        list_type=data.list_type,
        sector=data.sector,
        ticker=data.ticker,
        company_name=data.company_name,
        reason=data.reason,
    )
    return entry


@exclusions_router.put("/{entry_id}", response_model=ExclusionListResponse)
def update_exclusion(
    entry_id: UUID,
    data: ExclusionListUpdate,
    user_id: UserID,
    db: Session = Depends(get_db),
):
    service = ExclusionListService(db)
    update_data = data.model_dump(exclude_unset=True)
    entry = service.update_entry(entry_id, user_id, **update_data)
    if not entry:
        raise HTTPException(status_code=404, detail="Exclusion entry not found")
    return entry


@exclusions_router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exclusion(entry_id: UUID, user_id: UserID, db: Session = Depends(get_db)):
    service = ExclusionListService(db)
    if not service.delete_entry(entry_id, user_id):
        raise HTTPException(status_code=404, detail="Exclusion entry not found")


# ─── ESG Portfolio ───────────────────────────────────────────────────────────

portfolio_router = APIRouter(prefix="/portfolio", tags=["esg-portfolio"])


@alerts_router.get("/alternatives/{ticker}", response_model=list[SustainableAlternativeResponse])
def get_alternatives(ticker: str, user_id: UserID, db: Session = Depends(get_db)):
    service = EsgPortfolioService(db)
    return service.get_sustainable_alternatives(user_id, ticker)


@portfolio_router.get("/screen", response_model=PortfolioScreenResponse)
def screen_portfolio(user_id: UserID, db: Session = Depends(get_db)):
    service = EsgPortfolioService(db)
    return service.screen_portfolio(user_id)


# Register nested routers
router.include_router(scores_router)
router.include_router(carbon_router)
router.include_router(alerts_router)
router.include_router(exclusions_router)
router.include_router(portfolio_router)

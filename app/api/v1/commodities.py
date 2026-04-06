"""
Commodities & Precious Metals API routes.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CommodityPosition, FuturesContract
from app.schemas.commodity_schemas import (
    CommodityPositionCreate,
    CommodityPositionResponse,
    CommodityPositionUpdate,
    CommoditySummaryResponse,
    ExpirationAlertResponse,
    FuturesContractCreate,
    FuturesContractResponse,
    FuturesContractUpdate,
    FuturesSummaryResponse,
    HistoricalDataResponse,
    InflationHedgeMetricsResponse,
    PreciousMetalsPricesResponse,
    SyncPricesResponse,
)
from app.services.commodity_service import (
    CommodityService,
    FuturesContractService,
    PreciousMetalsService,
)

router = APIRouter(prefix="/commodities", tags=["commodities"])

CurrentUser = Annotated[UUID, Depends(lambda: UUID("00000000-0000-0000-0000-000000000000"))]  # placeholder


def get_user_id() -> UUID:
    """Placeholder — real auth injected by router-level dependency."""
    return UUID("00000000-0000-0000-0000-000000000000")


UserID = Annotated[UUID, Depends(get_user_id)]


# ─── Commodity Positions ─────────────────────────────────────────────────────

positions_router = APIRouter(prefix="/positions", tags=["commodity-positions"])


@positions_router.post("", response_model=CommodityPositionResponse, status_code=status.HTTP_201_CREATED)
def create_position(data: CommodityPositionCreate, user_id: UserID, db: Session = Depends(get_db)):
    service = CommodityService(db)
    position = service.create_position(
        user_id=user_id,
        name=data.name,
        commodity_type=data.commodity_type,
        quantity=data.quantity,
        purchase_price=data.purchase_price,
        purchase_date=data.purchase_date,
        unit=data.unit,
        ticker=data.ticker,
        current_price=data.current_price,
        currency=data.currency,
        notes=data.notes,
    )
    return position


@positions_router.get("", response_model=list[CommodityPositionResponse])
def list_positions(user_id: UserID, db: Session = Depends(get_db)):
    service = CommodityService(db)
    return service.list_positions(user_id)


@positions_router.get("/summary", response_model=CommoditySummaryResponse)
def get_commodity_summary(user_id: UserID, db: Session = Depends(get_db)):
    service = CommodityService(db)
    return service.get_commodity_summary(user_id)


@positions_router.get("/sync-prices", response_model=SyncPricesResponse)
def sync_prices(user_id: UserID, db: Session = Depends(get_db)):
    service = CommodityService(db)
    return service.sync_prices(user_id)


@positions_router.get("/{position_id}", response_model=CommodityPositionResponse)
def get_position(position_id: UUID, user_id: UserID, db: Session = Depends(get_db)):
    service = CommodityService(db)
    position = service.get_position(position_id, user_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@positions_router.put("/{position_id}", response_model=CommodityPositionResponse)
def update_position(
    position_id: UUID,
    data: CommodityPositionUpdate,
    user_id: UserID,
    db: Session = Depends(get_db),
):
    service = CommodityService(db)
    update_data = data.model_dump(exclude_unset=True)
    position = service.update_position(position_id, user_id, **update_data)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@positions_router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(position_id: UUID, user_id: UserID, db: Session = Depends(get_db)):
    service = CommodityService(db)
    if not service.delete_position(position_id, user_id):
        raise HTTPException(status_code=404, detail="Position not found")


# ─── Futures Contracts ──────────────────────────────────────────────────────

futures_router = APIRouter(prefix="/futures", tags=["futures"])


@futures_router.post("", response_model=FuturesContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(data: FuturesContractCreate, user_id: UserID, db: Session = Depends(get_db)):
    service = FuturesContractService(db)
    contract = service.create_contract(
        user_id=user_id,
        name=data.name,
        commodity_type=data.commodity_type,
        contract_size=data.contract_size,
        contract_month=data.contract_month,
        expiration_date=data.expiration_date,
        entry_price=data.entry_price,
        position_type=data.position_type,
        ticker=data.ticker,
        margin_required=data.margin_required,
        notes=data.notes,
    )
    return contract


@futures_router.get("", response_model=list[FuturesContractResponse])
def list_contracts(user_id: UserID, db: Session = Depends(get_db)):
    service = FuturesContractService(db)
    return service.list_contracts(user_id)


@futures_router.get("/summary", response_model=FuturesSummaryResponse)
def get_futures_summary(user_id: UserID, db: Session = Depends(get_db)):
    service = FuturesContractService(db)
    return service.get_futures_summary(user_id)


@futures_router.get("/expiration-alerts", response_model=list[ExpirationAlertResponse])
def get_expiration_alerts(user_id: UserID, db: Session = Depends(get_db)):
    service = FuturesContractService(db)
    return service.get_expiration_alerts(user_id)


@futures_router.get("/{contract_id}", response_model=FuturesContractResponse)
def get_contract(contract_id: UUID, user_id: UserID, db: Session = Depends(get_db)):
    service = FuturesContractService(db)
    contract = service.get_contract(contract_id, user_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@futures_router.put("/{contract_id}", response_model=FuturesContractResponse)
def update_contract(
    contract_id: UUID,
    data: FuturesContractUpdate,
    user_id: UserID,
    db: Session = Depends(get_db),
):
    service = FuturesContractService(db)
    update_data = data.model_dump(exclude_unset=True)
    contract = service.update_contract(contract_id, user_id, **update_data)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@futures_router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(contract_id: UUID, user_id: UserID, db: Session = Depends(get_db)):
    service = FuturesContractService(db)
    if not service.delete_contract(contract_id, user_id):
        raise HTTPException(status_code=404, detail="Contract not found")


# ─── Precious Metals ─────────────────────────────────────────────────────────

metals_router = APIRouter(prefix="/precious-metals", tags=["precious-metals"])


@metals_router.get("/prices", response_model=PreciousMetalsPricesResponse)
def get_precious_metals_prices(db: Session = Depends(get_db)):
    service = PreciousMetalsService(db)
    return service.get_precious_metals_prices()


@metals_router.get("/history", response_model=HistoricalDataResponse)
def get_metal_history(metal: str = "gold", days: int = 365, db: Session = Depends(get_db)):
    service = PreciousMetalsService(db)
    data = service.get_historical_data(metal, days)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No data for metal: {metal}")
    return {"metal": metal, "data": data}


@metals_router.get("/inflation-hedge", response_model=InflationHedgeMetricsResponse)
def get_inflation_hedge_metrics(db: Session = Depends(get_db)):
    service = PreciousMetalsService(db)
    return service.get_inflation_hedge_metrics()


# Register nested routers
router.include_router(positions_router)
router.include_router(futures_router)
router.include_router(metals_router)

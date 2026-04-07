"""
Copy Trading & Social Trading API
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.copy_trading_service import CopyTradingService, PaperTradingService


router = APIRouter(prefix="/copy-trading", tags=["copy-trading"])


# Request Models
class TraderInfo(BaseModel):
    id: str
    annualized_return: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    followers_count: int


class CopyAllocationRequest(BaseModel):
    follower_capital: float
    trader_allocation_pct: float


class SyncTradeRequest(BaseModel):
    original_trade_value: float
    copy_ratio: float
    follower_capital: float


class RiskAssessmentRequest(BaseModel):
    positions: list
    total_capital: float


class PaperTradeRequest(BaseModel):
    symbol: str
    quantity: int
    price: float
    trade_type: str  # BUY or SELL


class PaperPerformanceRequest(BaseModel):
    initial_capital: float
    current_cash: float
    positions: dict
    current_prices: dict


# Endpoints
@router.post("/trader-score")
def get_trader_score(request: TraderInfo):
    """
    Calculate overall trader score (0-100) based on performance and popularity.
    """
    service = CopyTradingService()
    score = service.get_trader_score(
        win_rate=request.win_rate,
        sharpe_ratio=request.sharpe_ratio,
        max_drawdown=request.max_drawdown,
        followers_count=request.followers_count
    )
    return {
        "trader_id": request.id,
        **score
    }


@router.post("/copy-allocation")
def calculate_copy_allocation(request: CopyAllocationRequest):
    """
    Calculate how much capital to allocate when copying a trader.
    """
    if request.follower_capital <= 0:
        raise HTTPException(status_code=400, detail="Follower capital must be positive")

    service = CopyTradingService()
    result = service.calculate_copy_allocation(
        follower_capital=request.follower_capital,
        trader_allocation_pct=request.trader_allocation_pct
    )
    return result


@router.post("/sync-trade")
def sync_trade(request: SyncTradeRequest):
    """
    Calculate synchronized trade for follower based on copy ratio.
    """
    if request.copy_ratio <= 0 or request.copy_ratio > 1:
        raise HTTPException(status_code=400, detail="Copy ratio must be between 0 and 1")

    service = CopyTradingService()
    result = service.sync_trade(
        original_trade_value=request.original_trade_value,
        copy_ratio=request.copy_ratio,
        follower_capital=request.follower_capital
    )
    return result


@router.post("/risk-score")
def calculate_risk_score(request: RiskAssessmentRequest):
    """
    Calculate copy trading risk score for a trader.
    """
    if request.total_capital <= 0:
        raise HTTPException(status_code=400, detail="Total capital must be positive")

    service = CopyTradingService()
    result = service.calculate_risk_score(
        positions=request.positions,
        total_capital=request.total_capital
    )
    return result


@router.get("/leaderboard")
def get_leaderboard(
    sort_by: str = Query("score", description="Sort by: score, return, followers, win_rate"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get copy trading leaderboard.
    """
    # In production, would fetch from database
    return {
        "sort_by": sort_by,
        "limit": limit,
        "message": "Connect to user data for actual leaderboard"
    }


@router.post("/warnings")
def generate_copy_warnings(
    trader_drawdown: float = Query(...),
    trader_max_drawdown: float = Query(...),
    follower_allocation_pct: float = Query(...)
):
    """
    Generate risk warnings for copying a trader.
    """
    service = CopyTradingService()
    warnings = service.generate_copy_warning(
        trader_drawdown=trader_drawdown,
        trader_max_drawdown=trader_max_drawdown,
        follower_allocation_pct=follower_allocation_pct
    )
    return {"warnings": warnings}


# Paper Trading Endpoints
@router.post("/paper/create-account")
def create_paper_account(user_id: str = Query(...)):
    """
    Create a new paper trading account.
    """
    service = PaperTradingService()
    account = service.create_paper_account(user_id)
    return account


@router.post("/paper/execute-trade")
def execute_paper_trade(
    request: PaperTradeRequest,
    current_cash: float = Query(...),
    current_positions: str = Query(..., description="JSON string of positions dict")
):
    """
    Execute a paper trade.
    """
    import json
    try:
        positions = json.loads(current_positions)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid positions JSON")

    if request.trade_type not in ["BUY", "SELL"]:
        raise HTTPException(status_code=400, detail="Trade type must be BUY or SELL")
    if request.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    service = PaperTradingService()
    result = service.execute_paper_trade(
        symbol=request.symbol.upper(),
        quantity=request.quantity,
        price=request.price,
        trade_type=request.trade_type,
        current_cash=current_cash,
        current_positions=positions
    )
    return result


@router.post("/paper/performance")
def calculate_paper_performance(request: PaperPerformanceRequest):
    """
    Calculate paper trading performance.
    """
    service = PaperTradingService()
    result = service.calculate_paper_performance(
        initial_capital=request.initial_capital,
        current_cash=request.current_cash,
        positions=request.positions,
        current_prices=request.current_prices
    )
    return result


@router.post("/paper/compare")
def compare_paper_vs_real(
    paper_return_pct: float = Query(...),
    real_return_pct: float = Query(...)
):
    """
    Compare paper trading performance to real portfolio.
    """
    service = PaperTradingService()
    result = service.compare_vs_real(paper_return_pct, real_return_pct)
    return result

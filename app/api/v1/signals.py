"""
AI Signals API routes.

Provides AI-powered stock signal scoring (1-100) with key drivers.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.signal_scoring_service import SignalScoringService

router = APIRouter(prefix="/signals", tags=["signals"])
logger = logging.getLogger(__name__)


class SignalScoreResponse(BaseModel):
    """Response model for signal score endpoint."""
    symbol: str
    score: int  # 1-100
    verdict: str  # "Buy", "Sell", "Hold"
    confidence: str  # "High", "Medium", "Low"
    key_drivers: list[str]
    indicator_scores: dict[str, float]
    period: str
    interval: str


@router.get("/{symbol}/score", response_model=SignalScoreResponse)
async def get_signal_score(
    symbol: str,
    period: str = Query(
        "3mo", description="Time period for calculation: 1d, 5d, 1mo, 3mo, 6mo, 1y"
    ),
    interval: str = Query("1d", description="Data interval: 1d, 1wk"),
) -> SignalScoreResponse:
    """
    Get AI-powered signal score (1-100) for a stock.

    Score ranges:
    - Buy: 70-100
    - Hold: 30-69
    - Sell: 1-29

    Args:
        symbol: Stock symbol (e.g., AAPL, 2330.TW)
        period: Time period for calculation
        interval: Data interval

    Returns:
        SignalScoreResponse with score, verdict, and key drivers
    """
    service = SignalScoringService()
    try:
        result = await service.calculate_score(symbol.upper(), period=period, interval=interval)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol {symbol} not found or insufficient data"
            )

        return SignalScoreResponse(
            symbol=result.symbol,
            score=result.score,
            verdict=result.verdict,
            confidence=result.confidence,
            key_drivers=result.key_drivers,
            indicator_scores=result.indicator_scores,
            period=period,
            interval=interval,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating signal score for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate signal score: {str(e)}")


@router.get("/batch/scores")
async def get_batch_signal_scores(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    period: str = Query(
        "3mo", description="Time period for calculation: 1d, 5d, 1mo, 3mo, 6mo, 1y"
    ),
    interval: str = Query("1d", description="Data interval: 1d, 1wk"),
) -> dict:
    """
    Get signal scores for multiple stocks.

    Args:
        symbols: Comma-separated stock symbols (e.g., "AAPL,GOOGL,MSFT")
        period: Time period for calculation
        interval: Data interval

    Returns:
        Dict with scores for each symbol
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="No symbols provided")
    
    if len(symbol_list) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 symbols per request")

    service = SignalScoringService()
    results = {}

    for symbol in symbol_list:
        try:
            result = await service.calculate_score(symbol, period=period, interval=interval)
            if result:
                results[symbol] = {
                    "score": result.score,
                    "verdict": result.verdict,
                    "confidence": result.confidence,
                }
            else:
                results[symbol] = {"error": "Insufficient data or symbol not found"}
        except Exception as e:
            results[symbol] = {"error": str(e)}

    return {"results": results}

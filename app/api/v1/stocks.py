"""
Stock API routes.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas import EvaluateRequest, SimulationRequest, StockHistoryResponse, StockQuoteResponse
from app.services.yfinance_service import YFinanceService
from app.services.indicators_service import TechnicalIndicatorsService
from app.services.signal_engine_service import SignalEngineService, SignalType
from app.services.simulated_trading_service import SimulatedTradingService, SimulationConfig, RiskProfile

router = APIRouter(prefix="/stocks", tags=["stocks"])
logger = logging.getLogger(__name__)


# Known stock names for lookup (same as search endpoint)
STOCK_NAMES = {
    # US Stocks
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc.",
    "MSFT": "Microsoft Corporation",
    "AMZN": "Amazon.com Inc.",
    "TSLA": "Tesla Inc.",
    "NVDA": "NVIDIA Corporation",
    "META": "Meta Platforms Inc.",
    "NFLX": "Netflix Inc.",
    # Taiwan Stocks (TWSE)
    "2330.TW": "Taiwan Semiconductor (TSMC)",
    "2317.TW": "Hon Hai Precision (Foxconn)",
    "2454.TW": "MediaTek Inc.",
    "2308.TW": "Delta Electronics",
    "2371.TW": "Acer Inc.",
    "2498.TW": "HTC Corporation",
    "2609.TW": "Yang Ming Marine",
    "2618.TW": "Evergreen Marine",
    "2891.TW": "Cathay Financial",
    "0050.TW": "Yuanta/P-Shares Taiwan Top 50 ETF",
    "0056.TW": "Yuanta MSCI Taiwan ETF",
    # Market Indices
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq",
    "^DJI": "Dow Jones Industrial Average",
    "^TNX": "10-Year Treasury Yield",
}


def _get_market_state_display(state: Optional[str]) -> Optional[str]:
    """Convert market state to user-friendly display value."""
    if not state or state == "UNKNOWN":
        return None
    return state


@router.get("/{symbol}/quote", response_model=StockQuoteResponse)
async def get_stock_quote(symbol: str) -> StockQuoteResponse:
    """
    Get real-time stock quote.

    Args:
        symbol: Stock symbol (e.g., AAPL, 2330.TW)

    Returns:
        StockQuoteResponse with current price data
    """
    service = YFinanceService()
    normalized = symbol.upper()
    try:
        async with service:
            quote = await service.get_quote(normalized)
            if quote is None:
                raise HTTPException(
                    status_code=404, detail=f"Symbol {symbol} not found"
                )
            return StockQuoteResponse(
                symbol=quote.symbol,
                name=STOCK_NAMES.get(normalized),
                price=quote.price,
                volume=quote.volume,
                timestamp=quote.timestamp,
                market_state=_get_market_state_display(quote.market_state),
                change=quote.change,
                change_percent=quote.change_percent,
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quote: {str(e)}")


@router.get("/{symbol}/history", response_model=StockHistoryResponse)
async def get_stock_history(
    symbol: str,
    period: str = Query(
        "1mo", description="Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, 10y, ytd, max"
    ),
    interval: str = Query("1d", description="Interval: 1d, 1wk, 1mo"),
) -> StockHistoryResponse:
    """
    Get historical stock data.

    Args:
        symbol: Stock symbol
        period: Time period
        interval: Data interval

    Returns:
        StockHistoryResponse with historical price data
    """
    service = YFinanceService()
    try:
        async with service:
            history = await service.get_history(
                symbol.upper(), period=period, interval=interval
            )
            if history is None:
                raise HTTPException(
                    status_code=404, detail=f"Symbol {symbol} not found"
                )
            return StockHistoryResponse(
                symbol=history.symbol,
                timestamps=history.timestamps,
                opens=history.opens,
                highs=history.highs,
                lows=history.lows,
                closes=history.closes,
                volumes=history.volumes,
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch history: {str(e)}"
        )


@router.get("/search")
async def search_stocks(q: str = Query(..., min_length=1, description="Search query")):
    """
    Search for stocks (basic implementation).

    Args:
        q: Search query

    Returns:
        List of matching symbols
    """
    # US Stocks
    common_symbols = {
        "AAPL": "Apple Inc.",
        "GOOGL": "Alphabet Inc.",
        "MSFT": "Microsoft Corporation",
        "AMZN": "Amazon.com Inc.",
        "TSLA": "Tesla Inc.",
        "NVDA": "NVIDIA Corporation",
        "META": "Meta Platforms Inc.",
        "NFLX": "Netflix Inc.",
    }
    # Taiwan Stocks (TWSE) - supported via Yahoo Finance .TW suffix
    twse_symbols = {
        "2330.TW": "Taiwan Semiconductor (TSMC)",
        "2317.TW": "Hon Hai Precision (Foxconn)",
        "2454.TW": "MediaTek Inc.",
        "2308.TW": "Delta Electronics",
        "2371.TW": "Acer Inc.",
        "2498.TW": "HTC Corporation",
        "2609.TW": "Yang Ming Marine",
        "2618.TW": "Evergreen Marine",
        "2891.TW": "Cathay Financial",
        "0050.TW": "Yuanta/P-Shares Taiwan Top 50 ETF",
        "0056.TW": "Yuanta MSCI Taiwan ETF",
    }
    # Merge both dicts
    common_symbols.update(twse_symbols)
    results = [
        {"symbol": k, "name": v}
        for k, v in common_symbols.items()
        if q.upper() in k or q.upper() in v.upper()
    ]
    return {"results": results}


@router.get("/{symbol}/indicators")
async def get_stock_indicators(
    symbol: str,
    period: str = Query(
        "3mo", description="Time period for calculation: 1d, 5d, 1mo, 3mo, 6mo, 1y"
    ),
    interval: str = Query("1d", description="Data interval: 1d, 1wk"),
) -> dict:
    """
    Get technical indicators for a stock (RSI, MACD, MA).

    Args:
        symbol: Stock symbol
        period: Time period for calculation
        interval: Data interval

    Returns:
        Dict with RSI, MACD, SMA, EMA values
    """
    service = YFinanceService()
    try:
        async with service:
            history = await service.get_history(symbol.upper(), period=period, interval=interval)
            if history is None:
                raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
            
            if len(history.closes) < 26:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient data for indicators calculation"
                )

            indicators = TechnicalIndicatorsService.calculate_all_indicators(history.closes)
            
            return {
                "symbol": symbol.upper(),
                "period": period,
                "interval": interval,
                **indicators,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate indicators: {str(e)}")


@router.get("/{symbol}/signal")
async def get_stock_signal(
    symbol: str,
    period: str = Query(
        "3mo", description="Time period for calculation: 1d, 5d, 1mo, 3mo, 6mo, 1y"
    ),
    interval: str = Query("1d", description="Data interval: 1d, 1wk"),
) -> dict:
    """
    Get automated stock signal (buy/sell/hold recommendation).

    Uses technical indicators (RSI, MACD, SMA, EMA) to generate
    a trading signal with confidence level and detailed reasoning.

    Args:
        symbol: Stock symbol
        period: Time period for calculation
        interval: Data interval

    Returns:
        Dict with signal, confidence, and reasoning
    """
    service = SignalEngineService()
    try:
        result = await service.get_signal(symbol.upper(), period=period, interval=interval)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol {symbol} not found or insufficient data"
            )

        return {
            "symbol": result.symbol,
            "signal": result.overall_signal.value,
            "signal_label": _get_signal_label(result.overall_signal),
            "confidence": result.confidence,
            "summary": result.summary,
            "bullish_factors": result.bullish_factors,
            "bearish_factors": result.bearish_factors,
            "indicators": [
                {
                    "indicator": ind.indicator,
                    "value": ind.value,
                    "signal": ind.signal.value,
                    "reasoning": ind.reasoning,
                }
                for ind in result.indicators
            ],
            "period": period,
            "interval": interval,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get signal: {str(e)}")


def _get_signal_label(signal: SignalType) -> str:
    """Get human-readable label for signal."""
    labels = {
        SignalType.STRONG_BUY: "強烈買入",
        SignalType.BUY: "買入",
        SignalType.HOLD: "持有",
        SignalType.SELL: "賣出",
        SignalType.STRONG_SELL: "強烈賣出",
    }
    return labels.get(signal, "未知")


@router.post("/simulation/run")
async def run_simulation(request: SimulationRequest) -> dict:
    """
    Run a trading simulation.

    Args:
        symbols: List of stock symbols to simulate
        initial_capital: Starting capital (default $5000)
        duration_days: Simulation duration in days
        risk_profile: Risk profile (conservative/moderate/aggressive)

    Returns:
        Simulation results with trades and performance metrics
    """
    config = SimulationConfig(
        initial_capital=request.initial_capital,
        duration_days=request.duration_days,
        risk_profile=RiskProfile(request.risk_profile),
    )

    service = SimulatedTradingService()
    try:
        result = await service.run_simulation(request.symbols, config)

        return {
            "initial_capital": result.initial_capital,
            "final_capital": round(result.final_capital, 2),
            "total_return": round(result.total_return, 2),
            "total_return_percent": round(result.total_return_percent, 2),
            "num_trades": result.num_trades,
            "winning_trades": result.winning_trades,
            "losing_trades": result.losing_trades,
            "win_rate": round(result.win_rate, 1),
            "trades": [
                {
                    "id": t.id,
                    "timestamp": t.timestamp.isoformat(),
                    "symbol": t.symbol,
                    "action": t.action,
                    "shares": round(t.shares, 2),
                    "price": round(t.price, 2),
                    "total": round(t.total, 2),
                    "reason": t.reason,
                }
                for t in result.trades
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.post("/simulation/evaluate")
async def evaluate_for_simulation(request: EvaluateRequest) -> dict:
    """
    Quick evaluation of symbols for trading simulation.

    Args:
        symbols: List of stock symbols to evaluate
        initial_capital: Starting capital
        risk_profile: Risk profile (conservative/moderate/aggressive)

    Returns:
        Evaluation results for each symbol
    """
    config = SimulationConfig(
        initial_capital=request.initial_capital,
        risk_profile=RiskProfile(request.risk_profile),
    )

    service = SimulatedTradingService()
    results = []

    for symbol in request.symbols:
        try:
            eval_result = await service.quick_evaluate(symbol, config)
            results.append(eval_result)
        except Exception as e:
            results.append({
                "symbol": symbol,
                "should_buy": False,
                "reason": f"Error: {str(e)}",
            })

    return {
        "symbols": results,
        "config": {
            "initial_capital": initial_capital,
            "risk_profile": risk_profile,
        },
    }

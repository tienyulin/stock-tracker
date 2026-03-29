"""
Stock API routes.
"""

from fastapi import APIRouter, HTTPException, Query

from app.schemas import StockHistoryResponse, StockQuoteResponse
from app.services.yfinance_service import YFinanceService

router = APIRouter(prefix="/stocks", tags=["stocks"])


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
    try:
        async with service:
            quote = await service.get_quote(symbol.upper())
            if quote is None:
                raise HTTPException(
                    status_code=404, detail=f"Symbol {symbol} not found"
                )
            return StockQuoteResponse(
                symbol=quote.symbol,
                price=quote.price,
                volume=quote.volume,
                timestamp=quote.timestamp,
                market_state=quote.market_state,
            )
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
    # Basic search - in production would call a search API
    common_symbols = {
        "AAPL": "Apple Inc.",
        "GOOGL": "Alphabet Inc.",
        "MSFT": "Microsoft Corporation",
        "AMZN": "Amazon.com Inc.",
        "TSLA": "Tesla Inc.",
        "2330.TW": "Taiwan Semiconductor",
        "2454.TW": "MediaTek Inc.",
    }
    results = [
        {"symbol": k, "name": v}
        for k, v in common_symbols.items()
        if q.upper() in k or q.upper() in v.upper()
    ]
    return {"results": results}

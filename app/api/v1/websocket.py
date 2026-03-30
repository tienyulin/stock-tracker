"""
WebSocket endpoints for real-time stock price updates.

Provides WebSocket connections for live price streaming.
"""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.yfinance_service import YFinanceService

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)

# Connection manager for WebSocket clients
class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        # Map of symbol -> list of connected WebSockets
        self.active_connections: dict[str, list[WebSocket]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, symbol: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            if symbol not in self.active_connections:
                self.active_connections[symbol] = []
            self.active_connections[symbol].append(websocket)
        logger.info(f"WebSocket connected: {symbol}, total: {len(self.active_connections[symbol])}")

    async def disconnect(self, websocket: WebSocket, symbol: str):
        """Remove a WebSocket connection."""
        async with self._lock:
            if symbol in self.active_connections:
                if websocket in self.active_connections[symbol]:
                    self.active_connections[symbol].remove(websocket)
                if not self.active_connections[symbol]:
                    del self.active_connections[symbol]
        logger.info(f"WebSocket disconnected: {symbol}")

    async def broadcast_to_symbol(self, symbol: str, message: dict):
        """Broadcast a message to all connections for a symbol."""
        async with self._lock:
            connections = self.active_connections.get(symbol, []).copy()

        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected
        for conn in disconnected:
            await self.disconnect(conn, symbol)


manager = ConnectionManager()


@router.websocket("/ws/stocks/{symbol}")
async def websocket_stock_price(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time stock price updates.

    Connect: wss://api.example.com/ws/stocks/AAPL
    Subscribe: {"action": "subscribe", "symbols": ["AAPL", "GOOGL"]}
    Unsubscribe: {"action": "unsubscribe", "symbols": ["AAPL"]}

    Received messages (price updates):
    {
        "type": "price_update",
        "symbol": "AAPL",
        "price": 150.25,
        "change": 2.50,
        "change_percent": 1.69,
        "volume": 1000000,
        "timestamp": 1609459200
    }
    """
    symbol = symbol.upper()
    await manager.connect(websocket, symbol)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "symbol": symbol,
            "message": f"Subscribed to {symbol} price updates"
        })

        # Start background task to fetch and send price updates
        update_task = asyncio.create_task(_send_periodic_updates(websocket, symbol))

        # Listen for client messages (subscribe/unsubscribe)
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                action = message.get("action")
                if action == "subscribe":
                    # Handle additional subscriptions
                    for sym in message.get("symbols", []):
                        await manager.connect(websocket, sym.upper())
                    await websocket.send_json({
                        "type": "subscribed",
                        "symbols": message.get("symbols", [])
                    })
                elif action == "unsubscribe":
                    for sym in message.get("symbols", []):
                        await manager.disconnect(websocket, sym.upper())
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "symbols": message.get("symbols", [])
                    })
                elif action == "ping":
                    await websocket.send_json({"type": "pong"})

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected by client: {symbol}")
    except Exception as e:
        logger.error(f"WebSocket error for {symbol}: {e}")
    finally:
        update_task.cancel()
        await manager.disconnect(websocket, symbol)


async def _send_periodic_updates(websocket: WebSocket, symbol: str, interval: int = 60):
    """
    Background task to send periodic price updates.

    Args:
        websocket: WebSocket connection
        symbol: Stock symbol to track
        interval: Seconds between updates (default 60)
    """
    service = YFinanceService()

    try:
        while True:
            try:
                async with service:
                    quote = await service.get_quote(symbol)

                if quote:
                    await websocket.send_json({
                        "type": "price_update",
                        "symbol": quote.symbol,
                        "price": quote.price,
                        "change": quote.change,
                        "change_percent": quote.change_percent,
                        "volume": quote.volume,
                        "timestamp": quote.timestamp,
                        "market_state": quote.market_state
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch quote for {symbol}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Failed to fetch price: {str(e)}"
                })

            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        logger.debug(f"Periodic updates cancelled for {symbol}")
        raise


@router.get("/ws/status")
async def websocket_status():
    """Check WebSocket service status."""
    async with manager._lock:
        total_connections = sum(len(conns) for conns in manager.active_connections.values())
        symbols = list(manager.active_connections.keys())

    return {
        "status": "active",
        "total_connections": total_connections,
        "subscribed_symbols": symbols
    }

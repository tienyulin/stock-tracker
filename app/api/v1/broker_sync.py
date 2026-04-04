"""
Broker Sync API endpoints.
"""

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.rate_limiter import limiter, DEFAULT_RATE_LIMIT
from app.services.broker_sync_service import (
    BrokerSyncService,
    Brokerage,
    ConnectionStatus,
    broker_sync_service,
)
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/broker-sync", tags=["Broker Sync"])


class BrokerConnectionInput(BaseModel):
    """Input for creating a broker connection."""
    brokerage: str = Field(..., pattern="^(robinhood|fidelity|schwab|td_ameritrade|etrade|webull)$")


class BrokerConnectionResponse(BaseModel):
    """Response for broker connection."""
    connection_id: str
    brokerage: str
    status: str
    broker_account_id: Optional[str]
    last_sync_at: Optional[str]
    created_at: str


class OAuthUrlResponse(BaseModel):
    """Response with OAuth URL for brokerage connection."""
    brokerage: str
    oauth_url: str
    connection_id: str


class SyncResultResponse(BaseModel):
    """Response for sync operation."""
    connection_id: str
    success: bool
    holdings_imported: int
    holdings_updated: int
    holdings_failed: int
    last_sync: str
    error_message: Optional[str]


class BrokerHoldingResponse(BaseModel):
    """Response for a single holding."""
    symbol: str
    quantity: float
    account_id: str
    security_type: str
    cost_basis: Optional[float]
    current_value: Optional[float]


@router.get("/connections", response_model=list[BrokerConnectionResponse])
@limiter.limit(DEFAULT_RATE_LIMIT)
async def list_connections(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> list[BrokerConnectionResponse]:
    """
    List all broker connections for the current user.
    """
    user_id = current_user["sub"]
    connections = await broker_sync_service.get_user_connections(user_id)
    
    return [
        BrokerConnectionResponse(
            connection_id=c.connection_id,
            brokerage=c.brokerage.value,
            status=c.status.value,
            broker_account_id=c.broker_account_id,
            last_sync_at=c.last_sync_at.isoformat() if c.last_sync_at else None,
            created_at=c.created_at.isoformat(),
        )
        for c in connections
    ]


@router.get("/oauth-url/{brokerage}", response_model=OAuthUrlResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_oauth_url(
    request: Request,
    brokerage: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> OAuthUrlResponse:
    """
    Get OAuth URL for connecting a brokerage account.
    
    Redirects user to brokerage OAuth flow, then callback to /broker-sync/callback.
    """
    try:
        broker = Brokerage(brokerage)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported brokerage: {brokerage}"
        )
    
    user_id = current_user["sub"]
    
    # Generate a temporary connection ID for the OAuth callback
    temp_connection_id = str(uuid.uuid4())
    
    # Build callback URL
    callback_url = f"{request.base_url}api/v1/broker-sync/callback"
    
    oauth_url = broker_sync_service.get_oauth_url(
        brokerage=broker,
        user_id=user_id,
        redirect_uri=callback_url
    )
    
    return OAuthUrlResponse(
        brokerage=brokerage,
        oauth_url=oauth_url,
        connection_id=temp_connection_id,
    )


@router.post("/connections", response_model=BrokerConnectionResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def create_connection(
    request: Request,
    body: BrokerConnectionInput,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> BrokerConnectionResponse:
    """
    Create a new brokerage connection.
    
    This endpoint is called after OAuth callback with the authorization code.
    """
    user_id = current_user["sub"]
    
    try:
        broker = Brokerage(body.brokerage)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported brokerage: {body.brokerage}"
        )
    
    # In production, exchange auth code for tokens here
    # For now, create a demo connection
    connection = await broker_sync_service.create_connection(
        user_id=user_id,
        brokerage=broker,
        access_token="demo_access_token",
        refresh_token="demo_refresh_token",
        broker_account_id=f"demo_account_{user_id[:8]}",
    )
    
    return BrokerConnectionResponse(
        connection_id=connection.connection_id,
        brokerage=connection.brokerage.value,
        status=connection.status.value,
        broker_account_id=connection.broker_account_id,
        last_sync_at=connection.last_sync_at.isoformat() if connection.last_sync_at else None,
        created_at=connection.created_at.isoformat(),
    )


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def delete_connection(
    request: Request,
    connection_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Disconnect a brokerage connection.
    """
    user_id = current_user["sub"]
    deleted = await broker_sync_service.delete_connection(connection_id, user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )


@router.post("/connections/{connection_id}/sync", response_model=SyncResultResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def sync_connection(
    request: Request,
    connection_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> SyncResultResponse:
    """
    Trigger a manual sync of holdings from a brokerage connection.
    """
    user_id = current_user["sub"]
    
    # Verify connection belongs to user
    connection = await broker_sync_service.get_connection(connection_id, user_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    result = await broker_sync_service.sync_holdings(connection_id)
    
    return SyncResultResponse(
        connection_id=result.connection_id,
        success=result.success,
        holdings_imported=result.holdings_imported,
        holdings_updated=result.holdings_updated,
        holdings_failed=result.holdings_failed,
        last_sync=result.last_sync.isoformat(),
        error_message=result.error_message,
    )


@router.get("/supported-brokers", response_model=list[dict])
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_supported_brokers(request: Request) -> list[dict]:
    """
    Get list of supported brokerages.
    """
    brokers = [
        {"id": "robinhood", "name": "Robinhood", "status": "active"},
        {"id": "fidelity", "name": "Fidelity", "status": "active"},
        {"id": "schwab", "name": "Charles Schwab", "status": "active"},
        {"id": "td_ameritrade", "name": "TD Ameritrade", "status": "active"},
        {"id": "etrade", "name": "E*TRADE", "status": "coming_soon"},
        {"id": "webull", "name": "Webull", "status": "coming_soon"},
    ]
    return brokers

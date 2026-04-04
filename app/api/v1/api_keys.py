"""
API Key management endpoints.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limiter import limiter, DEFAULT_RATE_LIMIT
from app.services.api_key_service import (
    create_api_key,
    get_user_api_keys,
    update_api_key,
    delete_api_key,
)
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


class CreateApiKeyRequest(BaseModel):
    """Request model for creating an API key."""
    name: str = Field(..., min_length=1, max_length=100, description="Name for the API key (e.g., 'Postman', 'Trading Bot')")
    rate_limit: int = Field(default=100, ge=10, le=10000, description="Requests per minute")
    expires_in_days: int | None = Field(default=None, ge=1, description="Days until expiration (optional)")


class CreateApiKeyResponse(BaseModel):
    """Response model for created API key."""
    id: uuid.UUID
    name: str
    key_prefix: str
    full_key: str = Field(..., description="The full API key - shown only once!")
    rate_limit: int
    expires_at: str | None
    created_at: str


class ApiKeyResponse(BaseModel):
    """Response model for API key (without the actual key)."""
    id: uuid.UUID
    name: str
    key_prefix: str
    rate_limit: int
    is_active: bool
    last_used_at: str | None
    created_at: str
    expires_at: str | None


class UpdateApiKeyRequest(BaseModel):
    """Request model for updating an API key."""
    name: str | None = Field(default=None, min_length=1, max_length=100)
    rate_limit: int | None = Field(default=None, ge=10, le=10000)
    is_active: bool | None = None


@router.post("", response_model=CreateApiKeyResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def create_api_key_endpoint(
    request: Request,
    body: CreateApiKeyRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create a new API key.
    
    The full API key is returned only once - save it securely!
    """
    api_key, full_key = await create_api_key(
        db=db,
        user_id=uuid.UUID(current_user["sub"]),
        name=body.name,
        rate_limit=body.rate_limit,
        expires_in_days=body.expires_in_days,
    )
    
    expires_at_str = None
    if api_key.expires_at:
        expires_at_str = api_key.expires_at.isoformat()
    
    return CreateApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        full_key=full_key,
        rate_limit=api_key.rate_limit,
        expires_at=expires_at_str,
        created_at=api_key.created_at.isoformat(),
    )


@router.get("", response_model=list[ApiKeyResponse])
@limiter.limit(DEFAULT_RATE_LIMIT)
async def list_api_keys(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all API keys for the current user."""
    keys = await get_user_api_keys(db=db, user_id=uuid.UUID(current_user["sub"]))
    
    return [
        ApiKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            rate_limit=k.rate_limit,
            is_active=k.is_active,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            created_at=k.created_at.isoformat(),
            expires_at=k.expires_at.isoformat() if k.expires_at else None,
        )
        for k in keys
    ]


@router.patch("/{key_id}", response_model=ApiKeyResponse)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def update_api_key_endpoint(
    request: Request,
    key_id: uuid.UUID,
    body: UpdateApiKeyRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update an API key."""
    api_key = await update_api_key(
        db=db,
        api_key_id=key_id,
        user_id=uuid.UUID(current_user["sub"]),
        name=body.name,
        rate_limit=body.rate_limit,
        is_active=body.is_active,
    )
    
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    
    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        rate_limit=api_key.rate_limit,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
        created_at=api_key.created_at.isoformat(),
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def delete_api_key_endpoint(
    request: Request,
    key_id: uuid.UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an API key."""
    deleted = await delete_api_key(
        db=db,
        api_key_id=key_id,
        user_id=uuid.UUID(current_user["sub"]),
    )
    
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

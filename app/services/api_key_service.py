"""
API Key service for management.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ApiKey


def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key.
    Returns (full_key, key_hash).
    The full key is shown only once to the user.
    """
    full_key = f"st_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:12]
    return full_key, key_hash, key_prefix


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA256."""
    return hashlib.sha256(key.encode()).hexdigest()


async def create_api_key(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    rate_limit: int = 100,
    expires_in_days: Optional[int] = None,
) -> tuple[ApiKey, str]:
    """
    Create a new API key for a user.
    Returns (ApiKey, full_key) - full_key is only available once.
    """
    full_key, key_hash, key_prefix = generate_api_key()
    
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    api_key = ApiKey(
        user_id=user_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
        rate_limit=rate_limit,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    
    return api_key, full_key


async def get_user_api_keys(db: AsyncSession, user_id: uuid.UUID) -> list[ApiKey]:
    """Get all API keys for a user."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())


async def get_api_key_by_hash(db: AsyncSession, key: str) -> Optional[ApiKey]:
    """Get an API key by its hash (for authentication)."""
    key_hash = hash_api_key(key)
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True,
        )
    )
    api_key = result.scalar_one_or_none()
    
    # Check expiration
    if api_key and api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return None
    
    return api_key


async def update_api_key(
    db: AsyncSession,
    api_key_id: uuid.UUID,
    user_id: uuid.UUID,
    name: Optional[str] = None,
    rate_limit: Optional[int] = None,
    is_active: Optional[bool] = None,
) -> Optional[ApiKey]:
    """Update an API key."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == api_key_id,
            ApiKey.user_id == user_id,
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        return None
    
    if name is not None:
        api_key.name = name
    if rate_limit is not None:
        api_key.rate_limit = rate_limit
    if is_active is not None:
        api_key.is_active = is_active
    
    await db.commit()
    await db.refresh(api_key)
    return api_key


async def delete_api_key(db: AsyncSession, api_key_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Delete an API key."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == api_key_id,
            ApiKey.user_id == user_id,
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        return False
    
    await db.delete(api_key)
    await db.commit()
    return True


async def update_last_used(db: AsyncSession, api_key: ApiKey) -> None:
    """Update the last used timestamp of an API key."""
    api_key.last_used_at = datetime.utcnow()
    await db.commit()

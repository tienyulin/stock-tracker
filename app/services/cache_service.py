"""
In-memory caching service with TTL support.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CacheEntry:
    """Cache entry with value and expiration time."""
    value: Any
    expires_at: float


class CacheService:
    """
    Simple in-memory cache with TTL (time-to-live) support.
    
    Thread-safe for async operations.
    """

    def __init__(self, default_ttl: float = 60.0):
        """
        Initialize cache service.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 60s).
        """
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value or None if not found/expired.
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            # Check if expired
            if time.time() > entry.expires_at:
                del self._cache[key]
                return None
            
            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds. Uses default_ttl if None.
        """
        ttl = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + ttl
        
        async with self._lock:
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key.
            
        Returns:
            True if key was deleted, False if not found.
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed.
        """
        now = time.time()
        removed = 0
        
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if now > entry.expires_at
            ]
            for key in expired_keys:
                del self._cache[key]
                removed += 1
        
        return removed

    async def get_or_set(self, key: str, factory, ttl: Optional[float] = None) -> Any:
        """
        Get from cache or compute and cache if not present.
        
        Args:
            key: Cache key.
            factory: Async function to compute value if not cached.
            ttl: Time-to-live in seconds.
            
        Returns:
            Cached or computed value.
        """
        value = await self.get(key)
        if value is not None:
            return value
        
        # Compute value
        value = await factory()
        await self.set(key, value, ttl)
        return value


# Global cache instance for stock quotes
stock_quote_cache = CacheService(default_ttl=30.0)  # 30 second TTL for quotes

# Global cache for stock history (longer TTL)
stock_history_cache = CacheService(default_ttl=300.0)  # 5 minute TTL for history
